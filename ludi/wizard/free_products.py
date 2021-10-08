# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.tools.float_utils import float_compare
from odoo.exceptions import UserError, ValidationError
from datetime import datetime,date,time,timedelta

import logging
_logger = logging.getLogger(__name__)


class LudiFreeProducts(models.TransientModel):
    _name = 'ludi.free'
    
    purchase_id = fields.Many2one('purchase.order','Compra')
    partner_id = fields.Many2one('res.partner','Proveedor')
    amount_purchase = fields.Float('Monto total')
    amount_left = fields.Float('Monto para Comprar',compute='compute_values_products_to_add')
    products_added = fields.One2many('ludi.free.line','free_id','Productos')
    
    
    @api.depends('products_added')
    def compute_values_products_to_add(self):
        for value in self:
            value.amount_left = value.amount_purchase -  sum(self.products_added.mapped('total'))
            
    def add_productos_to_purchase(self):
        if self.amount_left <= 0:
            lines = []
            discount_ids = self.purchase_id.promotion_ids.filtered(lambda x: x.apply_type == 'discount_products')
            for p in self.products_added:
                lines.append((0,0,{
                    'free_products':True,
                    'product_id':p.product_id.id,
                    'product_qty':p.product_qty,
                    'date_planned': self.purchase_id.date_planned,
                    'product_uom':p.product_uom.id,
                    'price_unit': p.price_unit,
                    'discount_ids': discount_ids,
                    'product_amount': True
                }))
            if lines:
                self.purchase_id.update({
                    'amount_purchase': 0,
                    'order_line':lines
                })
        else:
            raise ValidationError(('Aún cuenta con saldo positivo favor'))
        
        
    def cancel(self):
        return {'type': 'ir.actions.act_window_close'}
    
class LudiFreeProductsLine(models.TransientModel):
    _name = 'ludi.free.line'
    
    free_id = fields.Many2one('ludi.free','Gratis')
    partner_id = fields.Many2one('res.partner','Proveedor')
    product_id = fields.Many2one('product.product','Producto',domain="[('seller_ids.name','=',partner_id)]")
    product_qty = fields.Float('Cantidad',default=1)
    product_uom = fields.Many2one('uom.uom',related='product_id.uom_po_id')
    price_unit = fields.Float('Precio')
    total = fields.Float('Total',compute='compute_value_product')
    
    
    @api.onchange('product_id')
    def onchange_values_with_product_id(self):
        if self.product_id:
            self.price_unit = self.product_id._select_seller(partner_id=self.partner_id, quantity=self.product_qty, date=date.today(), uom_id=self.product_uom).price
            

    @api.depends('product_id','product_qty','price_unit','partner_id')
    def compute_value_product(self):
        for value in self:
            value.total = value.product_qty * value.price_unit
    
    
    