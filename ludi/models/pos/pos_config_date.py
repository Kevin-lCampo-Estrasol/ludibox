#-*-co# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import date, datetime,timedelta

class PosConfigDateLudi(models.Model):
    _name = 'pos.config.date'
    
    """
    date = fields.Date('Date')
    config_id = fields.Many2one('pos.confing')
    name = fields.Char()
"""
    date_plan = fields.Date('Fecha')
    pos_config_id = fields.Many2one(
        string='Pos Config',
        comodel_name='pos.config',
        
    )
    authorize = fields.Boolean('Autorizado',copy=False)
    authorize_by = fields.Many2one('res.users','Autorizado por')

    def write(self,vals):
        res = super(PosConfigDateLudi, self).write(vals)
        if 'authorize' in vals:
            if self.authorize == True:
                self.env['pos.config.date'].search([('id','=',self.id)]).copy({
                    'date_plan': self.date_plan + timedelta(days=7),
                })
                self.authorize_by = self.env.user.id
        return res