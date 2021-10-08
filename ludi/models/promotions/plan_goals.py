# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class LudiPlanGoals(models.Model):
    _name = 'plan.goals'
    
    name = fields.Char('Nombre')
    amount = fields.Float('Monto menta')
    porcent = fields.Float('Descuento %')
    promotion_id = fields.Many2one('ludi.product.promotion','Promoción')
    