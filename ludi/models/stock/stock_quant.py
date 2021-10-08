from odoo import models, fields, api, _
from odoo.exceptions import UserError,ValidationError
from datetime import datetime,date,time,timedelta
import itertools

class StockQuantLudi(models.Model):
    _inherit = 'stock.quant'


    brand_id = fields.Many2one('ludi.brand','Brand', related='product_id.brand',store=True,readonly=True)
    

    def stock_return_notification(self):
        stock_return = self.env['stock.quant'].search([]).filtered(lambda x: x.location_id.return_location == True)
        stock_group_admin = self.env.ref('stock.group_stock_manager')
        for users in stock_group_admin.users:
            if stock_return:
                message = "Existen mercancías en una ubicación de retorno"
                users.send_channel_message(message)
                
 