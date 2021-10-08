# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime,date,time,timedelta
import logging
_logger = logging.getLogger(__name__)



class LudiProductTemplate(models.Model):
    _inherit = 'product.template'

    is_temporal = fields.Boolean('Temporal time')
    temporality_ids = fields.Many2many(
        string='Temporalities',
        comodel_name='ludi.product.temporality',
        relation='ludi_product_temporality_relation',
    )
    max_purchase = fields.Float('Max Purchase')
    brand = fields.Many2one('ludi.brand','Marca')
    temporality_product = fields.Selection([('0','0'),('1','1')],'Temporality')
    favorite_sku = fields.Boolean('Favorito')
    seller_ids = fields.One2many('product.supplierinfo','product_tmpl_id')
    variant_seller_ids = fields.One2many('product.supplierinfo','product_tmpl_id')
    promotions_ids = fields.Many2many(
        string="Promociones y Descuentos",
        comodel_name='ludi.product.promotion',
        relation='product_template_promotion_rel',
    )
    uom_ids = fields.Many2many(
        string='Unidades de Medida',
        comodel_name='uom.uom',
        relation='product_uom_relation',
    )
    
    @api.onchange('uom_id','uom_po_id')
    def update_uom_ids_values(self):
        values = []
        if self.uom_id.id not in values:
           values.append(self.uom_id.id) 
        if self.uom_po_id not in values:
            values.append(self.uom_po_id.id)
        self.uom_ids = [(6,0,values)]
    

    def toggle_active(self):
        res = super(LudiProductTemplate, self).toggle_active()
        if self.env.user.id in self.env.ref('ludi.partner_ludi_personal').users.ids:
            return res
        else:
            return {'warning': {
                'title': _("Warning"),
                'message': _("No tiene permiso para archivar o desarchivar") ,
                }
            }
            
    def write(self,vals):
        res = super(LudiProductTemplate, self).write(vals)
        if 'standard_price' in vals:
            pricelist = self.env['product.pricelist.item'].search([('product_tmpl_id','=',self.id)])
            if pricelist:
                for p in pricelist:
                    p.onchange_value_cost_product()
                    p.compute_cost_with_discounts()
                    p.onchange_fixed_price_to_sell()
        if 'active' in vals:
            groups = self.env.ref('ludi.partner_ludi_personal').users.filtered(lambda x: x.id == self.env.user.id)
            if groups:
                return res
            else: 
                raise ValidationError(('No tiene permiso para archivar o restaurar este producto, solicite permiso'))
        if 'favorite_sku' in  vals:
            products = self.env['product.template'].search([('favorite_sku','=',True)])
            if len(products) <= 100:
                return res
            else:
                raise ValidationError(('Ya cuenta con 100 productos registradas como favoritas'))

    def action_promotion_product(self):
        today = date.today()
        products = self.env['product.template'].search([]).filtered(lambda x: x.temporality_ids)
        for p in products:
            for t in p.temporality_ids:
                new_date_begin = date(today.year,t.month_begin,t.day_begin)
                new_date_end = date(today.year,t.month_end,t.day_begin)
                if new_date_begin >= today and new_date_end <= today:
                    p.temporality_product = '1'
    
    def action_ludi_execute_methods(self):
        self.action_announce()
        self.action_send_mail()


    
    def action_announce(self):
        today = date.today()
        contacts = self.env['res.partner'].search([('x_notify_temporality','=',True)])
        for c in contacts:
            _logger.info('Entra Conctact '+c.name)
            temporality = self.env['ludi.product.temporality'].search([])
            for t in temporality:
                _logger.info('Entra Temporalidad '+t.name)
                message = False
                date_begin = date(today.year,t.month_begin,t.day_begin)
                date_end = date(today.year,t.month_end,t.day_begin)
                user = self.env['res.users'].sudo().search([('partner_id','=',c.id)])
                products = self.env['product.product'].search([('temporality_ids','in',[t.id])])
                if today == date_begin-timedelta(days=30) and products:
                    message="Faltan 30 días para el inicio de la temporada "+t.name    
                elif today == date_begin-timedelta(days=15) and products:
                    message="Faltan 15 días para el inicio de la temporada "+t.name
                elif today >= date_begin and today <= date_end  and products:
                    message="La temporada actual es "+t.name
                elif today >= date_end+timedelta(days=1) and today <=date_end+timedelta(days=30):
                    message = "La temporada "+t.name+" ha concluido, favor de verificar todos los productos sean retirados, para su devolución con proveedor"
                if user and message != False:
                    user.sudo().send_channel_message(message)
     
    
    def action_send_mail(self):
        today = date.today()
        contacts = self.env['res.partner'].search([('x_notify_temporality','=',True)])
        if contacts:
            for c in contacts:
                temporality = self.env['ludi.product.temporality'].search([])
                if temporality:
                    for t in temporality:
                        date_begin = date(today.year,t.month_begin,t.day_begin)
                        date_end = date(today.year,t.month_end,t.day_begin)
                        if today == date_begin-timedelta(days=30):
                            subject = "Faltan 30 días para el incio de la temporada de "+t.name
                            body = "<p>Faltan 30 días para la temporada de  %s y con ella los siguientes productos:</p>" %(t.name)
                            products = self.env['product.product'].search([('temporality_ids','in',[t.id])])
                            if products:
                                for p in products:
                                    sku = ''
                                    marca=''
                                    if p.default_code:
                                        sku=p.default_code
                                    if p.brand.name:
                                        marca = p.brand.name
                                    body+="<p><strong>SKU:</strong> %s, <strong>Marca:</strong> %s, <strong>Nombre:</strong> %s, <strong>Cantidad:</strong> %s</p>" %(sku,marca,p.name,p.qty_available)
                            else:
                                body = False

                        elif today == date_begin-timedelta(days=15):
                            
                            subject = "Faltan 15 días para el incio de la temporada de "+t.name
                            body = "<p>Faltan 15 días para la temporada %s y con ella los siguientes productos: </p>" %(t.name)
                            products = self.env['product.product'].search([('temporality_ids','in',[t.id])])
                            if products:
                                for p in products:
                                    sku = ''
                                    marca=''
                                    if p.default_code:
                                        sku=p.default_code
                                    if p.brand:
                                        marca = p.brand.name
                                    body+="<p><strong>SKU:</strong> %s, <strong>Marca:</strong> %s, <strong>Nombre:</strong> %s, <strong>Cantidad:</strong> %s</p>" %(sku,marca,p.name,p.qty_available)
                            else:
                                body = False
                        elif today >= date_begin and today <= date_end:
                          
                            subject = "La temporada "+t.name+" está activa actualmente"
                            body = "<p>La temporada %s se encuentra activa con los siguientes productos: </p>" %(t.name)
                            products = self.env['product.product'].search([('temporality_ids','in',[t.id])])
                            if products:
                                for p in products:
                                    sku = ''
                                    marca=''
                                    if p.default_code:
                                        sku=p.default_code
                                    if p.brand:
                                        marca = p.brand.name
                                    body+="<p><strong>SKU:</strong> %s, <strong>Marca:</strong> %s, <strong>Nombre:</strong> %s, <strong>Cantidad:</strong> %i</p>" %(sku,marca,p.name,p.qty_available)
                            else:
                                body = False
                        
                        elif today >= date_end+timedelta(days=1) and today <=date_end+timedelta(days=30):
                            subject = "La temporada "+t.name+"ha terminado, favor de retirar y verificar que los siguientes productos hayan sido retirados para su devolución de proveedor"
                            body = "<p>La temporada %s se encuentra activa con los siguientes productos: </p>" %(t.name)
                            products = self.env['product.product'].search([('temporality_ids','in',[t.id])])
                            if products:
                                for p in products:
                                    sku = ''
                                    marca=''
                                    if p.default_code:
                                        sku=p.default_code
                                    if p.brand:
                                        marca = p.brand.name
                                    body+="<p><strong>SKU:</strong> %s, <strong>Marca:</strong> %s, <strong>Nombre:</strong> %s, <strong>Cantidad:</strong> %i</p>" %(sku,marca,p.name,p.qty_available)
                            else:
                                body = False
                        
                    if body != False:
                        email_values={
                            'email_to':c.email,
                            'body_html':body,
                            'subject': subject  
                        }
                        mail_template = self.env.ref('ludi.ludi_email_temporality_mail_send').id
                        template = self.env['mail.template'].browse(mail_template)
                        template.send_mail(c.id, force_send=True, email_values=email_values)
                            
                                


                
                
    
