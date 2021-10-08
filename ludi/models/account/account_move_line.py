from odoo import models, fields, api, _
from odoo.exceptions import UserError

class LudiAccountLine(models.Model):
    _inherit = 'account.move.line'
    
    discount_ids = fields.Many2many('ludi.product.promotion','ludi_order_line_invoice_discounts',string='Descuento')

    