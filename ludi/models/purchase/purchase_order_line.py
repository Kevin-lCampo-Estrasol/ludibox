# -*- coding:utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError,ValidationError
from datetime import datetime,date,time,timedelta
import pytz
import logging
_logger = logging.getLogger(__name__)



class LudiPurchaseOrderline(models.Model):
    _inherit = 'purchase.order.line'


    restriction = fields.Boolean('Restriction',default=True)
    
    
    product_track = fields.Selection(related='product_id.tracking')
    expiration_date = fields.Boolean('Fecha Expiración',related='product_id.use_expiration_date')
    discount_ids = fields.Many2many('ludi.product.promotion','ludi_order_line_purchase_discounts',string='Descuento')
    free_products = fields.Boolean('Mercancía sin cargo')
    father_line = fields.Many2one('purchase.order.line',string='Línea Padre')
    product_amount = fields.Boolean('Producto Gratis de monto')
        

    @api.onchange('restricion','product_id','product_qty','price_unit')
    def onchange_values_product(self):
        _logger.info('Entraol')
        purchases = self.env['purchase.order.line'].search([('product_id','=',self.product_id.id),('order_id','!=',self.order_id.id)])
        if not purchases:
            price = self.price_unit
            total = self.product_qty * price
            if total > 30000 and self.restriction == True:
                total = 30000/self.price_unit
                self.product_qty = total
                self.price_unit = price
                warning = {
                    'title': _("Warning"),
                    'message': _("No puede comprar más de $30,000 en mercancía, la máxima cantidad que puede comprar es "+str(total))                
                }
                result = {'warning': warning}
                return result
        else:
            date = purchases[-1].order_id.effective_date.date()
            today = date.today()
            if today == date:
                price = self.price_unit
                total = self.product_qty * price
                if total > 30000 and self.restriction == True:
                    total = 30000/self.price_unit
                    self.product_qty = total
                    self.price_unit = price
                    warning = {
                        'title': _("Warning"),
                        'message': _("No puede comprar más de $30,000 en mercancía, la máxima cantidad que puede comprar es "+str(total))                
                    }
                result = {'warning': warning}
                return result
            
    @api.depends('product_qty', 'price_unit', 'taxes_id','discount_ids')
    def _compute_amount(self):
        for line in self:
            vals = line._prepare_compute_all_values()
            taxes = line.taxes_id.compute_all(
                vals['price_unit'],
                vals['currency_id'],
                vals['product_qty'],
                vals['product'],
                vals['partner'])
          
            subtotal = 0 if line.free_products == True else taxes['total_excluded']
            
            if self.discount_ids:
                for d in self.discount_ids:
                    if d.apply_type == 'purchase_subtotal':
                        subtotal= subtotal -  subtotal*(d.discount/100)
            tax = 0.0
            for t in line.taxes_id:
                tax = tax + (subtotal * (t.amount/100))
            line.update({
                'price_tax': tax,
                'price_total': subtotal+tax,
                'price_subtotal':  subtotal,
            })

    def add_product_promotion(self,product_id,date):
        promotions = self.env['ludi.product.promotion'].search([
            '|',('product_ids','=',product_id.id),('product_ids','=',False),
            ('partner_id','=',self.partner_id.id),
            '|',('date_begin','>=',date),('date_begin','=',False),
            '|',('date_end','<=',date),('date_end','=',False),
            ('in_purchase','=',True)
        ])
        if promotions and self.free_products == False:
            self.discount_ids = [(6, 0, promotions.ids)]


    @api.onchange('product_id','partner_id')
    def onchange_product_id_product_qty_values(self):
        if self.product_id:
            today = datetime.now().astimezone(pytz.timezone("America/Mexico_City")).date()
            self.discount_ids = False
            self.add_product_promotion(self.product_id,today)

    