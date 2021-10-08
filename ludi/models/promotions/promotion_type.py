# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError


class LudiProductsWithOutCarge(models.Model):
    _name = 'ludi.promotion.type'
    
    
    name = fields.Char('Nombre')
    type_prom = fields.Selection(string='Tipo', selection=[
        ('products','Mercancía sin cargo'),
        ('invoice','Descuento Factura'),
        ('credit_note','Nota de Crédito'),
        ('ant_inv','Descuento por Pago anticipado'),
        ('purchase_subtotal','Descuento Subtotal'),
        ('purchase_product','Descuento Producto'),
        ('price_unit_original','Descuento sobre el precio original'),
        ('products2','X En X Mercancía sin cargo'),
        ('discount_products','Mercancía sin cargo en base al monto'),
        ('plan','Plan de Crecimiento')
        ])
    