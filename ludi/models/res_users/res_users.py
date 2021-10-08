from odoo import models, fields, api, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)



class LudiResUsers(models.Model):
    _inherit = 'res.users'

    wishlist_ids = fields.Many2many('product.product','product_wishlit_values',domain=[('type','=','product')])


    def send_channel_message(self,message):
        ch_obj = self.env['mail.channel'].sudo().search([('name','=','OdooBot, '+self.name)])
        _logger.info('Ch obj = '+str(ch_obj))
        odoobot_id = self.env['ir.model.data'].xmlid_to_res_id("base.partner_root")
        ch_obj.sudo().message_post(body=message, author_id=odoobot_id, message_type="comment", subtype_xmlid="mail.mt_comment")
        
        

    