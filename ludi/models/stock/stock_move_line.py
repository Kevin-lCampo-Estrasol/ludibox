from odoo import models, fields, api, _
from odoo.exceptions import UserError

class LudiStockMoveLine(models.Model):
    _inherit = 'stock.move.line'
    
    related_expiration_date = fields.Datetime(related='lot_id.expiration_date', string='Fecha expiración')
    pending_product = fields.Float('Cantidad Pendiente',compute='compute_pending_product')
    
    
    def compute_pending_product(self):
        for value in self:
            total = value.product_qty - value.qty_done 
            if total <= 0:
                value.pending_product = 0
            else:
                value.pending_product = total

    
  