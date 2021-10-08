from odoo import models, fields, api

class LudiWishlist(models.Model):
    _name = 'ludi.wishlist'

    user_id = fields.Many2one('res.users','User')
    product_id = fields.Many2one('product.product','Producto')
    quantity = fields.Float('Cantidad',digits=(32, 2),related='product_id.qty_available')
    image = fields.Binary(string='Imagen',related='product_id.image_128')
    brand_id = fields.Many2one('ludi.brand','Marca',related="product_id.brand")