# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.tools.float_utils import float_compare
from odoo.exceptions import UserError, ValidationError
from datetime import datetime,date,time,timedelta
import pytz

import logging
_logger = logging.getLogger(__name__)





class LudiShowCalendar(models.TransientModel):
    _name = 'ludi.calendar.view'
    
    
    purchase_id = fields.Many2one('purchase.order','Compra')
    partner_id = fields.Many2one('res.partner','Proveedor')
    date_planned  = fields.Datetime('Fecha')
    lines = fields.One2many('ludi.calendar.view.line','calendar_wiz','Lineas')
    
    
    @api.onchange('date_planned')
    def search_events_to_planned_recipts(self):
        mexico_tzinfo = pytz.timezone("America/Mexico_City")
        date_converted = self.date_planned.astimezone(mexico_tzinfo).date()
        location = self.env['stock.location'].sudo().search([('partner_ids','=',self.partner_id.id)])
        if location:
            event = self.env['calendar.event'].sudo().search([
                ('location_id','in',location.ids),
                ('inventory_event','=',True),
            ])
            _logger.info('Entra event = '+str(event))
            for e in event:
                start = e.start.astimezone(mexico_tzinfo).date()
                if start == date_converted:
                    self.update({
                        'lines': [(0,0,{
                            'name':'Ocupado',
                            'calendar_id':e.id,
                            'date_begin':e.start,
                            'date_end':e.stop

                        })]
                    })
                
    def apply_date_on_purchase(self):
        if self.purchase_id:
            self.purchase_id.date_to_delivery = self.date_planned
    
    def cancel(self):
        return {'type': 'ir.actions.act_window_close'}
        
    
class LudiShowCalendar(models.TransientModel):
    _name = 'ludi.calendar.view.line'
    
    name = fields.Char('Nombre')
    calendar_id = fields.Many2one('calendar.event','Calendario')
    date_begin  = fields.Datetime('Fecha de Inicio')
    date_end  = fields.Datetime('Fecha fin')
    calendar_wiz = fields.Many2one('ludi.calendar.view')
    
