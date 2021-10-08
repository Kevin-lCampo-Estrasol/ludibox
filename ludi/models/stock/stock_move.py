from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ludiStockMove(models.Model):
    _inherit = 'stock.move'
    
    type_move = fields.Selection(related='picking_type_id.code')
    product_cost = fields.Float(string='Coste', digits=(32, 2), related='purchase_line_id.price_unit')
    notes  = fields.Text('Comentarios')
    
    
  
    
    