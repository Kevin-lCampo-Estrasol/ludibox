from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ludiResPartner(models.Model):
    _inherit = 'res.partner'

    x_code_identi = fields.Char('Código de identificación')
    x_notify_temporality = fields.Boolean('Notify temporality')
    x_amount_sales = fields.Monetary(string='Total ventas',compute='compute_total_sales_value',store=True)
    x_credit_available = fields.Monetary('Crédito disponible',compute='compute_credit_available',store=True)
    
    
    @api.depends('sale_order_ids')
    def compute_total_sales_value(self):
        for value in self:
            total = sum(value.sale_order_ids.filtered(lambda x: x.invoice_status != 'invoiced' and x.state in ['sale','done']).mapped('amount_untaxed'))
            value.x_amount_sales = total
            
    @api.depends('credit_limit','x_amount_sales')
    def compute_credit_available(self):
        for value in self:
            value.x_credit_available = value.credit_limit - value.x_amount_sales
            
    
