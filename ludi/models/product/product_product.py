import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import date, timedelta
import logging
_logger = logging.getLogger(__name__)
from odoo.tools import float_is_zero, float_repr
from collections import defaultdict


class ludiProductProduct(models.Model):
    _inherit = 'product.product'
    
    @api.onchange('uom_id','uom_po_id')
    def update_uom_ids_values(self):
        values = []
        if self.uom_id.id not in values:
           values.append(self.uom_id.id) 
        if self.uom_po_id not in values:
            values.append(self.uom_po_id.id)
        self.uom_ids = [(6,0,values)]

    def toggle_active(self):
        _logger.info('Entra')
        """ Archiving related product.template if there is not any more active product.product
        (and vice versa, unarchiving the related product template if there is now an active product.product) """
        result = super( ludiProductProduct, self).toggle_active()
        if self.active == False:
            groups = self.env.ref('ludi.partner_ludi_personal').users.filtered(lambda x: x.id == self.env.user.id)
            if groups:
                _logger.info('Entra 1')
                # We deactivate product templates which are active with no active variants.
                tmpl_to_deactivate = self.filtered(lambda product: (product.product_tmpl_id.active and not product.product_tmpl_id.product_variant_ids)).mapped('product_tmpl_id')
                # We activate product templates which are inactive with active variants.
                tmpl_to_activate = self.filtered(lambda product: (not product.product_tmpl_id.active and product.product_tmpl_id.product_variant_ids)).mapped('product_tmpl_id')
                (tmpl_to_deactivate + tmpl_to_activate).toggle_active()
                return result
            else:
                raise ValidationError(('No tiene permiso para restaurar este archivo, solicite permiso'))
            
            
    def write(self,vals):
        res = super( ludiProductProduct, self).write(vals)
        if 'standard_price' in vals :
            self.update_pricelist_methods()
        if 'active' in vals:
            groups = self.env.ref('ludi.partner_ludi_personal').users.filtered(lambda x: x.id == self.env.user.id)
            if groups:
                return res
            else: 
                raise ValidationError(('No tiene permiso para archivar o restaurar este producto, solicite permiso'))
            
    def update_pricelist_methods(self):
        pricelist = self.env['product.pricelist.item'].search([('product_id','=',self.id)])
        if pricelist:
            for p in pricelist:
                p.onchange_value_cost_product()
                p.compute_cost_with_discounts()
                p.onchange_fixed_price_to_sell()
                
    