#  -*- coding:utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ludiProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    cost = fields.Float('Costo', compute='onchange_value_cost_product')
    cost_with_discount = fields.Float('Costo con descuentos',compute='compute_cost_with_discounts')
    margin_win = fields.Float('Margen de ganancia')
    fixed_price = fields.Float(compute= 'onchange_fixed_price_to_sell', store=True,)
    

    @api.depends('product_tmpl_id','product_id','product_tmpl_id.promotions_ids','product_id.promotions_ids','product_tmpl_id.standard_price','product_id.standard_price')
    def onchange_value_cost_product(self):
        for value in self:
            value.cost = value.product_tmpl_id.standard_price if value.product_tmpl_id else value.product_id
        
    @api.depends('cost','product_tmpl_id','product_id','product_tmpl_id.promotions_ids','product_id.promotions_ids','product_tmpl_id.standard_price','product_id.standard_price')
    def compute_cost_with_discounts(self):
        for value in self:
            cost = 0
            if value.product_tmpl_id:
                if value.product_tmpl_id.promotions_ids:
                    cost_product = value.product_tmpl_id.standard_price if value.product_tmpl_id else 0
                    cost = cost_product if cost_product > 0 else 0
                    promotions = value.product_tmpl_id.promotions_ids.filtered(lambda x: x.price_client == 'yes')
                    if promotions:
                        for p in promotions:
                            cost = cost - (cost*(p.discount/100))
            if value.product_id:
                if value.product_id.promotions_ids:
                    cost_product = value.product_id.standard_price if value.product_id else 0
                    cost = cost_product if cost_product > 0 else 0
                    promotions = value.product_id.promotions_ids.filtered(lambda x: x.price_client == 'yes')
                    if promotions:
                        for p in promotions:
                            cost = cost - (cost*(p.discount/100))
            
            value.cost_with_discount = cost
            
    @api.depends('margin_win','product_tmpl_id','product_id','cost','product_tmpl_id.promotions_ids','product_id.promotions_ids','product_tmpl_id.standard_price','product_id.standard_price')
    def onchange_fixed_price_to_sell(self):
        for value in self:
            if value.margin_win > 0:
                win = value.margin_win/100
                value.fixed_price = value.cost + (value.cost * win)
            else:
                value.fixed_price = 0
    