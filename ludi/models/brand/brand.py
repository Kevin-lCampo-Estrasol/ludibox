from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class LudiBrand(models.Model):
    _name = 'ludi.brand'
    _rec_name = 'name'

    name = fields.Char(string='Nombre')
    name_sort = fields.Char('Nombre corto')
    product_ids = fields.One2many('product.template','brand','Productos')
    favorite = fields.Selection([('0','0'),('1','1')],'Favorito')
    
    
    def write(self,vals):
        res = super(LudiBrand, self).write(vals)
        if 'favorite' in vals:
            brands = self.env['ludi.brand'].search([('favorite','=','1')])
            if len(brands) <= 100:
                return res
            else:
                raise ValidationError(('Ya cuenta con 100 marcas registradas como favoritas'))