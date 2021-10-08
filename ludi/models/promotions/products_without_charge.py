# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime, date, timedelta

class LudiProductsWithOutCarge(models.Model):
    _name = 'ludi.products.free'
    
    partner_id = fields.Many2one('res.partner','Proveedor')
    product_id = fields.Many2one('product.product','Producto',domain="[('seller_ids.name','=',partner_id)]")
    product_qty = fields.Float(digits=(32, 2),string='Cantidad',default=1)
    cost = fields.Float(digits=(32, 2),string='Costo',default=1)
    price_unit = fields.Float(digits=(32, 2),string='Precio',default=1)
    product_uom_id = fields.Many2one('uom.uom',string='UdM',related='product_id.uom_po_id',readonly=True,store=True)
    promotion_id = fields.Many2one('ludi.product.promotion','Promoción')
    subtotal = fields.Float(digits=(32, 2),string='Subtotal', compute='compute_total_subtotal')
    
   
   
    @api.onchange('product_id','product_qty')
    def onchange_cost_product(self):
        today = date.today()
        if self.product_id:
            supplierinfo = self.product_id._select_seller(partner_id=self.partner_id,quantity=self.product_qty,date=today,uom_id=self.product_uom_id)
            if supplierinfo:
                self.cost = supplierinfo.price
                self.price_unit = supplierinfo.price
            else:
                self.cost = self.product_id.standard_price
                

    @api.depends('cost','product_qty')
    def compute_total_subtotal(self):
        for value in self:
            value.subtotal = value.cost * value.product_qty