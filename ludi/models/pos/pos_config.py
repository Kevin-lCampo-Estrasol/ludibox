from odoo import models, fields, api, _
from odoo.exceptions import UserError,ValidationError
from datetime import date

class PosConfigLudi(models.Model):
    _inherit = 'pos.config'

    inventory_pl_ids =  fields.One2many(
        string='Planificar Inventarios',
        comodel_name='pos.config.date',
        inverse_name='pos_config_id',
    )

    def open_ui(self):
        today = date.today()
        planning = self.inventory_pl_ids.filtered(lambda x: x.date_plan == today and x.authorize == False)
        if planning:
            raise ValidationError('No se puede iniciar, Se tiene programado para el día de hoy inventario, solicite autorización')
        else:
            self.ensure_one()
        
            self._validate_fields(set(self._fields) - {"cash_control"})
            return {
                'type': 'ir.actions.act_url',
                'url': self._get_pos_base_url() + '?config_id=%d' % self.id,
                'target': 'self',
            }

