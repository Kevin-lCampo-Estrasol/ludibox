from odoo import models, fields, api, _
from odoo.exceptions import UserError,ValidationError

class LudiPosOrder(models.Model):
    _inherit = 'pos.order'

    @api.model
    def create(self,vals):
        res = super(LudiPosOrder, self).create(vals)
        if res.pos_session.cash_register_balance_end >= 5000:
            raise ValidationError(('No se puede crear venta ya tiene $5000 en efectivo'))
        else:
            return res
    

    