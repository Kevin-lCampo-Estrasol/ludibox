# -*- coding: utf-8 -*-
from odoo import models, fields, api
import calendar
from  datetime import datetime,date,time, timedelta
import logging
_logger = logging.getLogger(__name__)



class KudiTemporality(models.Model):
    _name = 'ludi.product.temporality'
    _rec_name = 'name'

    name = fields.Char(string='Nombre')
    day_begin = fields.Integer('Día inicio')
    month_begin = fields.Integer('Mes inicio')
    day_end = fields.Integer('Día fin')
    month_end = fields.Integer('Mes fin')


    @api.onchange('day_begin','month_begin')
    def onchange_day_month_begin_values(self):
        if self.day_begin > 0  and self.month_begin > 0:
            today = date.today()
            if self.month_begin > today.month:
                day_range = calendar.monthrange(today.year,self.month_begin)
            else:
                day_range = calendar.monthrange(today.year+1,self.month_begin)
            if self.day_begin > int(day_range[1]):
                self.day_begin = int(day_range[1])
        

    @api.onchange('day_end','month_end')
    def onchange_day_month_end_values(self):
        if self.day_end > 0 and self.month_end > 0:
            today = date.today()
            if self.month_end > today.month:
                day_range = calendar.monthrange(today.year,self.month_end)
            else:
                day_range = calendar.monthrange(today.year+1,self.month_end)
            if self.day_end > int(day_range[1]):
                self.day_end = int(day_range[1])

    

    @api.onchange('month_begin','month_end')
    def onchange_value_month(self):
        if self.month_begin > 12:
            self.month_begin = 12
        if self.month_end > 12:
            self.month_end = 12