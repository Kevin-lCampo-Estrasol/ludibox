from odoo import models, fields, api, _
from odoo.exceptions import UserError,ValidationError
from datetime import date

class PosSessionLudi(models.Model):
    _inherit = 'pos.session'

    def open_frontend_cb(self):
        today = date.today()
        planning = self.config_id.inventory_pl_ids.filtered(lambda x: x.date_plan == today)
        if planning:
            raise ValidationError('No se puede iniciar, Se tiene programado para el día de hoy inventario')
        else:
            if not self.ids:
                return {}
            return {
                'type': 'ir.actions.act_url',
                'target': 'self',
                'url': self.config_id._get_pos_base_url() + '?config_id=%d' % self.config_id.id,
            }
            