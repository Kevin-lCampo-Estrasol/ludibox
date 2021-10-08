from odoo import models, fields, api, _
from odoo.exceptions import UserError,ValidationError
from datetime import datetime

class LudiAccountMove(models.Model):
    _inherit = 'account.move'

    product_promotion_id = fields.Many2one('ludi.product.promotion',string='Promociones')
    promotion_ids = fields.Many2many('ludi.product.promotion','ludi_promotion_invoice_add_value',string="Agregar Promociones",copy=False)
    applied = fields.Boolean(
        string='Aplicado',
    )
    
    
    def apply_values_in_purchase(self):
        if self.promotion_ids and self.applied == False:
            for promotion in self.promotion_ids:
                if promotion.apply_type in ['invoice','credit_note','ant_inv','purchase_subtotal','purchase_product','price_unit_original']:
                    for line in self.invoice_line_ids:
                        if promotion.product_ids:
                            if line.product_id.id in promotion.product_ids.ids:
                                line.update({'discount_ids':[(4, promotion.id)]})
                        else:
                            line.update({'discount_ids':[(4, promotion.id)]})                        
            self.applied = True   
        else:
            raise ValidationError(('No se pudo complentar la operación, no existen promociones o ya están aplicadas'))
        
    def action_register_payment(self):
        res = super(LudiAccountMove, self).action_register_payment()
        result = self.picking_no_delivery(self.partner_id.id,datetime.now())
        if result == True:
            return res
        else:
            raise ValidationError(('No puede registrar pago , existen mercancías que aún no han sido entregadas'))
        
    def picking_no_delivery(self,partner_id,date):
        picking = self.env['stock.picking'].search([
        ('partner_id','=',partner_id),
        ('free_products','=',True),
        ('state','not in',['done','cancel']),
        ('picking_type_code','=','incoming')
        ])
        if picking.filtered(lambda x: date > x.scheduled_date):
            return False
        else:
            return True
    