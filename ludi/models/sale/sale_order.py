from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class LudiSaleOrder(models.Model):
    _inherit = 'sale.order'
    
    credit_available = fields.Monetary('Crédito disponible',related='partner_id.x_credit_available')
    credit_after_sale = fields.Monetary('Crédito después de venta',compute='compute_values_after_sale')
    code_identi = fields.Char('Código de identificación',related='partner_id.x_code_identi')
    
    @api.model
    def create(self,vals):
        res = super(LudiSaleOrder, self).create(vals)
        res.partner_id.compute_total_sales_value()
        res.partner_id.compute_credit_available()
        return res
    
    
    def write(self,vals):
        res = super(LudiSaleOrder, self).write(vals)
        self.partner_id.compute_total_sales_value()
        self.partner_id.compute_credit_available()
        return res
    
    
    @api.depends('amount_untaxed','credit_available','payment_term_id')
    def compute_values_after_sale(self):
        for value in self:
            total_amount = value.credit_available - value.amount_untaxed
            if value.payment_term_id.id == 1:
                total_amount = 0
            value.credit_after_sale = total_amount

    @api.onchange('payment_term_id')
    def _on_change_payment(self):
        _logger.info("ON change state")
        for rec in self:
            _logger.info("refinself")
            #_logger.info("SELF: ")
            #_logger.info( self.id)
            #_logger.info(self)
        mail_search = self.env.ref('ludi.notify_sale').id
        template = self.env['mail.template'].browse(mail_search)
        #template.send_mail(self.id,force_send=True)

        #for value in self:
        #    _logger.info(value.state)
        #    if value.state == 'sent':
        #        _logger.info("Presupuesto enviado")

    @api.model
    def notify_promos_job(self):
        _logger.info("NOTIFYYY PROMOS JOOOB")
        user = self.env['res.users'].search( [('id','=', '2')] )
        message = """Promociones activas: 
                    """
        
        promo_list = self.env['coupon.program'].search([])
        for promo in promo_list:
            _logger.info(promo.name)
            message = message + promo.name + """
            """
        user.send_channel_message(message)
    
    def send_channel_message(self,message):
        ch_obj = self.env['mail.channel'].sudo().search([('name','=','OdooBot, '+self.name)])
        _logger.info('Ch obj = '+str(ch_obj))
        odoobot_id = self.env['ir.model.data'].xmlid_to_res_id("base.partner_root")
        ch_obj.sudo().message_post(body=message, author_id=odoobot_id, message_type="comment", subtype_xmlid="mail.mt_comment")
        

class LudiSaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure', domain="[]")
    
    @api.onchange('product_id','product_uom',)
    def onchange_filterd_value(self):
        res = {'domain':{'product_uom':[('category_id', '=', self.product_uom_category_id.id)]}}
        if self.product_id:
            uom = self.product_id.uom_ids.mapped('id')
            res = {'domain':{'product_uom':[('id', 'in', uom)]}} if uom else {'domain':{'product_uom':[('category_id', '=', self.product_uom_category_id.id)]}}
        return res
   


        
            
                
            
            