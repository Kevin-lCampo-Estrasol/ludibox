# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from odoo.tools import float_compare, date_utils, email_split, email_re
from odoo.tools.misc import formatLang, format_date, get_lang

from datetime import date, timedelta
from collections import defaultdict
from itertools import zip_longest
from hashlib import sha256
from json import dumps

import ast
import json
import re
import warnings



import logging
_logger = logging.getLogger(__name__)



class LudiPromotionsModel(models.Model):
    _name = 'ludi.product.promotion'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _rec_name = 'name'

    name = fields.Char(string='Nombre')
    date_begin = fields.Date('Fecha Inicio',tracking=True)
    date_end = fields.Date('Fecha Fin',tracking=True)
    apply_type = fields.Selection(string="tipo ",related='promotion_type_id.type_prom')
    description  = fields.Text('Descripción')
    discount_amount = fields.Float('Monto sin IVA',digits=(32, 2))
    products_without_charge = fields.One2many('ludi.products.free','promotion_id',string='Productos sin cargo')
    
    invoice_id = fields.Many2one('account.move',string='Factura')
    product_ids = fields.Many2many(
        comodel_name='product.product',
        relation='product_purchase_promotion_supplier',
        string='Productos Seleccionados',
        domain=" [('seller_ids.name.id','=',partner_id)]",
    )    
    invoice_credit_notes_ids = fields.One2many(
        string='Notas de Crédito',
        comodel_name='account.move',
        inverse_name='product_promotion_id',
    )
    invoice_date_end = fields.Date('Fecha de fin de la nota de crédito')
    payment_term_id = fields.Many2one('account.payment.term')
    state = fields.Selection([('draft', 'Creado'),
        ('authorized','Autorizado'),('done', 'Aplicado'),
        ('cancel','Cancelado')],default='draft',string='Estado',tracking=True)
    total_sales = fields.Float('Total Ventas',digits=(32,2),compute='compute_total_sales')
    discount = fields.Float(string='Descuento(%)',digits=(32,2))
    products_discount = fields.Boolean('Productos Seleccionados')
    active = fields.Boolean('Active',default=True)
    partner_id = fields.Many2one('res.partner','Proveedor',tracking=True)
    amount_subtotal = fields.Float(digits=(32, 2),string='Subtotal',compute='compute_total_product_without_carge')
    location_id = fields.Many2one('stock.location','Ubicación destino')
    stock_picking_id = fields.Many2one('stock.picking','Recepción de Mercancía')
    date_to_delivery = fields.Datetime('Fecha para entrega')
    promotion_type_id = fields.Many2one('ludi.promotion.type',string='Aplicar en:')
    in_purchase = fields.Boolean('Aplicar en compra')
    free_qty = fields.Float(string='Mercancía sin cargo')
    purchase_qty = fields.Float(string='Cantidad Máxima')
    price_client  = fields.Selection([('yes', 'Si'),('no','No')],'¿Aplica Precio al Cliente?')

    next_discount = fields.One2many('plan.goals','promotion_id',string='Metas descuento')
    paid_date = fields.Date('Fecha de Cobro')
    paid_with = fields.Selection([('credit_note', 'Nota de Crédito'),('free_products', 'Mercancía sin cargo')],string='Pagar con:')
    count_type = fields.Selection([('units', 'Unidades'),('price', 'Dinero')],string='Contabilizar')
    check_parametrer = fields.Selection([('purchase', 'Compras'),('sales', 'Ventas')],string='Verificar')
    total_units = fields.Float(string='Total Unidades',digits=(32,2),compute='compute_total_sales')
    
    @api.depends('check_parametrer','count_type','paid_with','date_begin','date_end')
    def compute_total_sales(self):
        for value in self:
            invoice = self.env['account.move'].search([('invoice_date','>=',value.date_begin),('invoice_date','<=',value.date_end)])
            _logger.info(str(invoice))
            products = value.mapped('product_ids').ids
            if value.check_parametrer == 'purchase' and invoice:
                purchase = invoice.filtered(lambda x: x.move_type == 'in_invoice')
                _logger.info(str(purchase))
                if purchase:
                    price = 0 if products else sum(purchase.invoice_line_ids.mapped('price_subtotal'))
                    units = 0 if products else sum(purchase.invoice_line_ids.mapped('quantity'))
                    if products:
                        for i in purchase:
                            for l in i.invoice_line_ids:
                                if l.product_id.id in products:
                                    units = units + l.quantity
                                    price = price + l.price_subtotal    
                    value.total_units = units
                    value.total_sales = price
                else:
                    value.total_sales = 0
                    value.total_units = 0
            elif value.check_parametrer == 'sales' and invoice:
                sales = invoice.filtered(lambda x: x.move_type == 'out_invoice' )
              
                if sales:
                    price = 0 if products else sum(sales.invoice_line_ids.mapped('price_subtotal'))
                    units = 0 if products else sum(sales.invoice_line_ids.mapped('quantity'))
                    if products:
                        for i in sales:
                            for l in i.invoice_line_ids:
                                if l.product_id.id in products:
                                    _logger.info('Entra 4')
                                    units = units + l.quantity
                                    price = price + l.price_subtotal    
                    value.total_units = units
                    value.total_sales = price
                else:
                    value.total_sales = 0
                    value.total_units = 0
            else:
                value.total_sales = 0
                value.total_units = 0
                 
                           
    def compute_and_apply_promotion(self):
        promotions = self.env['ludi.product.promotion'].search([('state','=','authorized'),('apply_type','=','plan')])
        for p in promotions:
            for goal in p.next_discount:
                if p.count_type == 'units':
                    if p.total_units >= goal.amount:
                        p.discount = goal.porcent
                        p.discount_amount = p.total_sales*(goal.porcent/100)
                elif p.count_type == 'price':
                    if p.total_sales >= goal.amount:
                        p.discount = goal.porcent
                        p.discount_amount = p.total_sales*(goal.porcent/100)
            if p.paid_date == date.today():
                if p.paid_with == 'credit_note':
                    p.generate_credit_note()
                else:
                    p.add_lines_purchase()
                    
                
            
    @api.onchange('total_sales','discount')
    def onchange_amount_with_total_sales(self):
        if self.total_sales > 0 and self.discount > 0:
            self.discount_amount = self.total_sales * (self.discount/100)

    def cron_execute_ludi_methods(self):
        self.archive_promotion_expired()
        self.notify_promotion_pendendant()

    def toggle_active(self):
        return super(LudiPromotionsModel, self).toggle_active()


    def archive_promotion_expired(self):
        today = date.today()
        promotions = self.env['ludi.product.promotion'].search([]).filtered(lambda x: today > x.date_end)
        if promotions:
            for p in promotions:
                p.toggle_active()


    def authorize(self):
        self.state = 'authorized'


    def action_create_credit_note(self):
        self.sudo().create_credit_note()
        
    def generate_credit_note(self):
        self.create_credit_note()
        self.state_done()


    def create_credit_note(self):
        journal = self.env['account.journal'].sudo().search([('name','in',['Vendor Bills','Cuentas por pagar'])])
        product = self.env['product.product'].search([('name','=','Cobro a proveedores')])
        plan =self.env['account.account'].search([('code','=','601.84.01')])
        account = self.env['account.move']
        if journal and product and plan:
            credit_note = account.create({
                'product_promotion_id':self.id,
                'partner_id': self.partner_id.id,
                'move_type': 'in_refund',
                'invoice_date': date.today(),
                'date': date.today(),
                'invoice_date_due': self.invoice_date_end,
                'invoice_payment_term_id': self.payment_term_id.id,
                'journal_id': journal.id,
                'invoice_line_ids':[(0,0,{
                    'product_id': product.id,
                    'name':self.description,
                    'account_id': plan.id,
                    'quantity': 1.00,
                    'product_uom_id': product.uom_id.id,
                    'tax_ids': product.supplier_taxes_id,
                    'price_unit': self.discount_amount
                })]

            })
            return credit_note if credit_note else ''
        
    
    @api.onchange('apply_type','discount')
    def onchange_value_total_discontun(self):
        if self.invoice_id and self.discount > 0 :
            self.discount_amount = self.invoice_id.amount_untaxed*(self.discount/100)
            
    
    def state_done(self):
        self.state = 'done'
        
    def state_cancel(self):
        self.state = 'cancel'

    def state_draft(self):
        self.state = 'draft'
        
        
    def open_form_view_credit_notes(self):
        view = {
            'name': ('Notas de crédito'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': [('product_promotion_id','=',self.id)],
        }
        return view

    def notify_promotion_pendendant(self):
        promotions = self.env['ludi.product.promotion'].search([('state','=','authorized')])
        admin = self.env['res.users'].search([('name','=','Administrator')])
        message = "Existen Promociones que aún no se les ha generado una nota de crédito, favor de verificarlas"
        if promotions and admin:
            admin.send_channel_message(admin,message)

    @api.depends('products_without_charge')
    def compute_total_product_without_carge(self):
        for value in self:
            total = 0
            for p in value.products_without_charge:
                total = total + p.subtotal
            value.amount_subtotal = total
        
    def add_lines_purchase(self):
        if self.discount_amount >= self.amount_subtotal:
            lines = []
            if self.products_without_charge:
                for p in self.products_without_charge:
                    total = p.product_qty
                    if p.product_id.uom_id.id != p.product_id.uom_po_id.id:
                        total = p.product_qty * p.product_id.uom_po_id.factor_inv    
                    lines.append((0,0,{
                        'product_id': p.product_id.id,
                        'name':p.product_id.name,
                        'product_uom_qty': total,
                        'product_uom':p.product_id.uom_id.id,
                    }))
                operation_picking = self.env['stock.picking.type'].search([('id','=',1)])
                if lines:
                    picking = self.env['stock.picking'].sudo().create({
                        'partner_id': self.partner_id.id,
                        'picking_type_id': operation_picking.id,
                        'location_id':4,
                        'location_dest_id': self.location_id.id,
                        'free_products': True,
                        'move_ids_without_package': lines,
                    })
                    if picking:
                        self.stock_picking_id = picking.id
                        
                        self.state_done()
                        
    
    def apply_credit_note_invoice(self):
        if self.invoice_id:
            note = self.create_credit_note()
            if note:
                note.action_post()
                
                
    @api.model
    def create(self,vals):
        res = super(LudiPromotionsModel, self).create(vals)
        if res.product_ids:
            for p in res.product_ids: 
                p.product_tmpl_id.update({'promotions_ids':[(4,res['id'])]})
                
        return res