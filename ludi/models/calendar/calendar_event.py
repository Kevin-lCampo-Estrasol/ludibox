# -*- coding:utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class LudiCalendarEvent(models.Model):
    _inherit = 'calendar.event'

    location_id = fields.Many2one('stock.location','Ubicación')
    inventory_event = fields.Boolean('Evento de inventario')
