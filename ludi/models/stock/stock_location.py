# -*- coding:utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class LudiStockLocation(models.Model):
    _inherit = 'stock.location'
    
    stock_user_ids = fields.Many2many(string='Usuarios',comodel_name='res.users',relation='stock_users_wroks',)
    partner_ids = fields.Many2many(string='Proveedores',comodel_name='res.partner',relation='location_partners_recipts',domain=[('supplier_rank','>','0')])
    
    
    
    
    

    