import logging
_logger = logging.getLogger(__name__)

import json
import time
import itertools
from ast import literal_eval
from collections import defaultdict
from datetime import datetime,date,time,timedelta
from itertools import groupby
from operator import itemgetter

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.addons.stock.models.stock_move import PROCUREMENT_PRIORITIES
from odoo.exceptions import UserError,ValidationError
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, format_datetime
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.tools.misc import format_date



class LudiStockPicking(models.Model):
    _inherit = 'stock.picking'
    
    
    operation_type  = fields.Selection(related='picking_type_id.code')
    no_validate_delivery = fields.Boolean('Autorizar Entrega',copy=False)
    return_products = fields.Boolean('Mercancía con retorno',copy=False)
    date_to_return = fields.Date('Fecha de retorno',copy=False)
    sale_to_internal = fields.Many2one('sale.order','Venta',copy=False)
    stock_picking_return = fields.Many2one('stock.picking','Regreso de mercancía')
    scheduled_date = fields.Datetime(copy=False)
    print_number = fields.Integer(string='Número de impresiones',default=0)
    free_products = fields.Boolean(string='Mercancía sin cargo')
    
    
    def send_message_product_recepction(self):
        if self.picking_type_id.code == 'incoming':
            brand = []
            for key,group in itertools.groupby(self.move_ids_without_package,key = lambda b: b.product_id.brand):
                user = []
                for g in group:
                    users =  self.env['res.users'].search([('wishlist_ids','in',g.product_id.id)])
                    for u in users:
                        if u not in user:
                            user.append(u.id)
                            
                if user:
                    usr = self.env['res.users'].search([('id','in',user)])
                    message = "La marca "+key.name+" cuenta con nuevas cantidades del inventario"
                    if usr and brand not in brand:
                        
                        for u in usr:
                            u.send_channel_message(message)
                        
    def button_validate(self):
        res = super(LudiStockPicking, self).button_validate()
        
        
        
        self.send_message_product_recepction()
        return res

    def action_cancel(self):
        res = super(LudiStockPicking, self).action_cancel()
        if self.operation_type == 'incoming':
            self.create_credit_note_cancel()
        return res

    def write(self,vals):
        res = super(LudiStockPicking, self).write(vals)
        today = datetime.now()
        
        if 'no_validate_delivery' in vals:
            if self.move_ids_without_package and self.no_validate_delivery == True:
                lines = []
                for p in self.move_ids_without_package:
                    if p.product_uom_qty != p.quantity_done:
                        total = p.product_uom_qty - p.quantity_done
                        lines.append((0,0,{
                            'product_id': p.product_id.id,
                            'name': p.name,
                            'product_uom_qty': total,
                            'price_unit': p.product_id.lst_price,
                            'tax_id':[(4,2)],
                            'product_uom': p.product_id.uom_id.id
                        }))
                if lines:
                    sale = self.env['sale.order'].sudo().create({
                        'partner_id': self.partner_id.id,
                        'validity_date': date(today.year,today.month,today.day)+timedelta(days=7),
                        'date_order':today,
                        'order_line':lines
                    })
                    self.sale_to_internal = sale.id
        return res
                    
    def notify_group_user_no_return_products(self):
        today = date.today()
        picking = self.env['stock.picking'].search([('return_products','=',True),('date_to_return','=',today)])
        group = self.env.ref('ludi.credit_and_payment').users
        if picking:
            no_return_mercancy = picking.filtered(lambda x: x.stock_picking_return.state != 'done')
            if no_return_mercancy:
                message = '<p> Existen mercancía en Mercancía con Retorno que no han sido devueltas'
                for stp in no_return_mercancy:
                    message += " "+stp.name+", "
                message += '</p>' 
                for user in group:
                    user.send_channel_message(message)
            
           
    def print_order(self):
        if self.operation_type in ['internal','outgoing']:
            if self.print_number == 0:
                self.print_number = self.print_number + 1
                return self.env.ref('stock.action_report_picking').report_action(self)
                
            elif self.print_number > 0 :
                if self.env.user.id in self.env.ref('stock.group_stock_manager').users.ids:
                    self.print_number = self.print_number + 1
                    return self.env.ref('stock.action_report_picking').report_action(self)
                else:
                    raise ValidationError(('No tiene permitido imprimir más de una vez esta orden'))
            else:
                raise ValidationError(('No tiene permitido imprimir más de una vez esta orden'))
        else:
            return self.env.ref('stock.action_report_picking').report_action(self)
    
    
    
    def create_credit_note_cancel(self):
        credit_note = self.env['account.move']
        lines = []
        plan =self.env['account.account'].sudo().search([('code','=','205.06.01')])
        journal = self.env['account.journal'].sudo().search([('name','in',['Vendor Bills','Cuentas por pagar'])])
        for move in self.move_ids_without_package:
            total = move.product_uom_qty - move.quantity_done
            if total > 0:
                price = move.product_id._select_seller(partner_id=self.partner_id,quantity=total,date=date.today(),uom_id=move.product_id.uom_po_id)
               
                lines.append((0,0,{
                    'product_id': move.product_id.id,
                    'name':move.description_picking,
                    'account_id': plan.id,
                    'product_uom_id':move.product_uom,
                    'quantity':total,
                    'price_unit': move.purchase_line_id.price_unit if  move.purchase_line_id else price.price,
                    'tax_ids': move.product_id.supplier_taxes_id,
                    'account_id': plan.id,
                }))
        if lines:
            credit_note.sudo().create({
                'partner_id': self.partner_id.id,
                'move_type': 'in_refund',
                'invoice_date': date.today(),
                'date': date.today(),
                'invoice_date_due': self.date_deadline,
                'invoice_origin': self.purchase_id.name if self.purchase_id else self.name,
                'journal_id': journal.id,
                'invoice_line_ids':lines
            })
    
    