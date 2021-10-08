# -*- coding:utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class LudiComission(models.Model):
    _name = 'ludi.comission'
    
    
    user_id = fields.Many2one('res.users','Usuario')
    

    