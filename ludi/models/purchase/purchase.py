from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime,date,time,timedelta
import pytz

import logging
_logger = logging.getLogger(__name__)



class LudiPurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    
    date = date.today()
    
    date_to_delivery  = fields.Datetime('Fecha de tentativa',default=lambda x: datetime.now())
    authorize_delivery = fields.Boolean(string='Autorización fecha de entraga',copy=False)
    calendar_id = fields.Many2one('calendar.event','Calendario',copy=False)
    location_id = fields.Many2one('stock.location','Ubicación',domain="[('partner_ids','=',partner_id)]")
    down_payment = fields.Boolean('Requiere pago anticipado',copy=False)
    promotion_ids = fields.Many2many('ludi.product.promotion','ludi_promotion_purchase_add_value',string="Agregar Promociones")
    applied = fields.Boolean('Aplicado',copy=False)
    amount_purchase = fields.Float('Monto para mercancía gratis')
    promotion_ap_ids = fields.Many2many('ludi.product.promotion','ludi_promotion_purchase_promotion_post_purchase',string="Agregar Promociones",
                                        domain = "[('in_purchase','=',True),('partner_id','=',partner_id),('id','not in',promotion_ids)]")
    pending_promotions = fields.Boolean('Promociones Pendientes',compute='_compute_value_to_define_promotions')
    
    @api.depends('partner_id')
    def _compute_value_to_define_promotions(self):
        for value in self:
            credit_note = self.env['account.move'].sudo().search([('partner_id','=',value.partner_id.id),('move_type','=','in_refund'),('payment_state','!=','paid')])
            value.pending_promotions = True if credit_note else False
            

    @api.onchange('partner_id')
    def onchange_values_availale(self):
        if self.promotion_ids and self.applied == False:
            self.promotion_ids = False
        elif self.promotion_ids and self.applied == True:
            raise ValidationError(('No puede cambiar de proveedor una vez que ya aplico las promociones'))
     
       
    @api.onchange('down_payment','date_to_delivery')
    def onchange_value_delivery(self):
        today = date.today()
        delivery = self.date_to_delivery
        if self.down_payment == True:
            if delivery.date() >= today and delivery.date() <= today+timedelta(days=15):
                pass
            else:
                self.date_to_delivery = today+timedelta(days=15)
                
    def change_authorize_delivery(self):
        mexico_tzinfo = pytz.timezone("America/Mexico_City")
        self.date_planned = self.date_to_delivery
        date = self.date_to_delivery.astimezone(mexico_tzinfo).date()
        
        events = self.env['calendar.event'].search([('partner_ids.id','=',self.env.user.partner_id.id),('location_id','=',self.location_id.id)])
        
        calendar = []
        for e in events:
            start_cast = e.start.astimezone(mexico_tzinfo).date()           
            if start_cast == date:
                calendar.append(e.id)
       
        if len(calendar) < 4:
            doc = False
            docs = events.search([('id','in',calendar)])
            for e in docs:
                if e.start >= self.date_to_delivery and e.stop <= self.date_to_delivery:
                    doc = True
                    break
                elif e.start >= self.date_to_delivery+timedelta(hours=1) and e.stop <= self.date_to_delivery+timedelta(hours=1):
                    doc = True
                    break
            if doc == True:
                raise ValidationError(('Ya tiene un eventos planeado para esa fecha y esa hora, favor de cambiarlo'))
            else:
                calendar = self.env['calendar.event'].create({
                'name': 'Entrega de mercancía '+self.partner_id.name,
                'partner_ids':[(4,self.env.user.partner_id.id),(4,self.partner_id.id)],
                'start': self.date_to_delivery,
                'location': self.location_id.name,
                'location_id': self.location_id.id,
                'alarm_ids': [(4,self.env.ref('calendar.alarm_notif_5').id),],
                'stop': self.date_to_delivery+timedelta(hours=1),
                'inventory_event':True,
                })
                self.authorize_delivery = True
                self.calendar_id = calendar.id
        else:
            raise ValidationError(('Demasiadas fechas para el mismo día, favor de cambiar la fecha para la recepción'))
    
    def button_cancel(self):
        for order in self:
            for inv in order.invoice_ids:
                if inv and inv.state not in ('cancel', 'draft'):
                    raise UserError(_("Unable to cancel this purchase order. You must first cancel the related vendor bills."))
        if self.calendar_id:
            self.calendar_id.unlink()
        
        self.write({'state': 'cancel','authorize_delivery':False})

    def send_all_purchase_order_date_to_delivery(self):
        today = date.today()
        mexico_tzinfo = pytz.timezone("America/Mexico_City")
        purchases = self.env['purchase.order'].search([('state','in',['purchase','done'])])
        if purchases:
            subject = 'Recepción de mercancías para hoy'
            message = ''
            for p in purchases:
                date_r= p.date_to_delivery.astimezone(mexico_tzinfo).date()
                if date_r == today:   
                    if p.order_line.filtered(lambda x: x.qty_received != x.product_qty):
                        message += "<p>Pedido de compra <strong>"+p.name+"</strong></p>"
                        for line in p.order_line:
                            if line.qty_received != line.product_qty:
                                qty = line.product_qty-line.qty_received
                                message +="<p><strong>Producto: </strong>"+line.product_id.name+", <strong>Cantidad: </strong>"+str(qty)+" "+line.product_uom.name+"</p>"
            if message != '':
                for user in self.env.ref('stock.group_stock_user').users:
                    if user.id in self.location_id.stock_user_ids.ids:
                       
                        email_values = {
                            'email_to': user.login,
                            'body_html': message,
                            'subject': subject
                        }
                        mail_template = self.env.ref('ludi.ludi_purchase_date_recipt').id
                        template = self.env['mail.template'].browse(mail_template)
                        template.send_mail(p.id,force_send=True,email_values=email_values)
                    
                    
    def open_wizard_calendar(self):
        view = {
            'name': ('Lista fechas'),
            'view_type':'form',
            'view_mode':'form',
            'res_model':'ludi.calendar.view',
            'type': 'ir.actions.act_window',
            'target':'new',
            'context':{
                'default_purchase_id':self.id,
                'default_partner_id':self.partner_id.id,
                'default_date_planned':self.date_to_delivery
            }
        }
        return view
    
    def open_wizard_free_products(self):
        view = {
            'name': ('Agregar productos'),
            'view_type':'form',
            'view_mode':'form',
            'res_model':'ludi.free',
            'type': 'ir.actions.act_window',
            'target':'new',
            'context':{
                'default_purchase_id':self.id,
                'default_partner_id':self.partner_id.id,
                'default_amount_purchase':self.amount_purchase
            }
        }
        return view
        
    
    
    def send_mail_change_notification(self):
        if self.env.user.partner_id.id == self.partner_id.id:
            users = self.env.ref('purchase.group_purchase_user').users
            for u in users:
                email_values = {
                    'email_from': self.env.user.login,
                    'email_to': u.login,  
                }
                mail_template = self.env.ref('ludi.ludi_purchase_change_value_supplier').id
                template = self.env['mail.template'].browse(mail_template)
                template.send_mail(self.id,force_send=True,email_values=email_values)
    
    
    def write(self,vals):
        res = super(LudiPurchaseOrder, self).write(vals)
        
        self.sudo().send_mail_change_notification()
        if 'order_line' in vals:
            lines = self.order_line.filtered(lambda x: x.free_products == True and x.product_amount == False and x.product_qty == 0)
            if lines:
                lines.unlink()
            for line in self.order_line:
                if line.free_products == True and line.product_amount == False:
                    product_online = self.order_line.filtered(lambda x: x.product_id == line.product_id and x.free_products == False)
                    if not product_online:
                        line.unlink()

        result = self.picking_no_delivery(self.partner_id.id,datetime.now())
        
        if result == False:
            raise ValidationError(('No puede completar la creación de esta compra, existen mercancías que aún no han sido entregadas'))
        else:
            self.sudo().send_mail_change_notification()
            return res
        
    
    @api.model
    def create(self,vals):
        res = super(LudiPurchaseOrder, self).create(vals)
        if res.order_line:
            lines = res.order_line.filtered(lambda x: x.free_products == True and x.product_amount == False and x.product_qty == 0)
            if lines:
                lines.unlink()
        result = res.picking_no_delivery(res.partner_id.id, datetime.now())
        
        if result == False:
            raise ValidationError(('No puede completar la creación de esta compra, existen mercancías que aún no han sido entregadas'))
        else:
            return res
    

    def _prepare_invoice(self):
        """Prepare the dict of values to create the new invoice for a purchase order.
        """
        self.ensure_one()
        move_type = self._context.get('default_move_type', 'in_invoice')
        journal = self.env['account.move'].with_context(default_move_type=move_type)._get_default_journal()
        if not journal:
            raise UserError(_('Please define an accounting purchase journal for the company %s (%s).') % (self.company_id.name, self.company_id.id))

        partner_invoice_id = self.partner_id.address_get(['invoice'])['invoice']
        invoice_vals = {
            'ref': self.partner_ref or '',
            'move_type': move_type,
            'narration': self.notes,
            'currency_id': self.currency_id.id,
            'invoice_user_id': self.user_id and self.user_id.id,
            'partner_id': partner_invoice_id,
            'fiscal_position_id': (self.fiscal_position_id or self.fiscal_position_id.get_fiscal_position(partner_invoice_id)).id,
            'payment_reference': self.partner_ref or '',
            'partner_bank_id': self.partner_id.bank_ids[:1].id,
            'invoice_origin': self.name,
            'invoice_payment_term_id': self.payment_term_id.id,
            'invoice_line_ids': [],
            'promotion_ids': self.promotion_ap_ids,
            'company_id': self.company_id.id,
        }
        return invoice_vals
    
    @api.onchange('order_line','order_line.product_id','order_line.product_qty','order_line.price_unit','order_line.discount_ids')
    def onchange_apply_promotions_order_line(self):
        promotions = []
        promotions_ap = []
        today = date.today()
        promot = self.env['ludi.product.promotion'].search([
                ('partner_id','=',self.partner_id.id),
                '|',('date_begin','>=',today),('date_begin','=',False),
                '|',('date_end','<=',today),('date_end','=',False),
                ('in_purchase','=',False)
            ])
        if promot:
            self.promotion_ap_ids = [(6, 0, promot.ids)]
        self.promotion_ids = False
        self.amount_purchase = 0
        for line in self.order_line:
            price_unit = line.product_id._select_seller(partner_id=self.partner_id, quantity=line.product_qty, date=date.today(), uom_id=line.product_uom).price
            if line.free_products == False:    
                for d in line.discount_ids:
                    add = (4,d.id)
                    if d.apply_type == 'products':
                        add_lines = []      
                        for product in d.products_without_charge:
                            add_lines.append((0,0,{
                                'free_products': True,
                                'product_id': product.product_id.id,
                                'name': product.product_id.name,
                                'date_planned':self.date_planned,
                                'product_uom_qty':  product.product_qty,
                                'price_unit':price_unit,
                            }))
                    if d.apply_type == 'invoice':
                        if add not in promotions_ap:
                            promotions_ap.append(add)
                    if d.apply_type == 'credit_note':
                        if add not in promotions_ap:
                            promotions_ap.append(add)
                    if d.apply_type == 'ant_inv':
                        if add not in promotions_ap:
                            promotions_ap.append(add)
                    if d.apply_type == 'purchase_product':
                        price_unit = price_unit - (price_unit*(d.discount/100))
                        line.price_unit =  price_unit
                    if d.apply_type == 'price_unit_original':
                        price = line.product_id._select_seller(partner_id=self.partner_id, quantity=line.product_qty, date=date.today(), uom_id=line.product_uom).price
                        discount = d.discount
                        value = (price*(discount/100))
                        price_unit = price_unit - value
                        line.price_unit = price_unit
                    if d.apply_type == 'products2':
                        if d.free_qty > 0 and d.purchase_qty > 0:
                            qty = int(line.product_qty/d.purchase_qty) * d.free_qty
                            if qty > 0:
                                pol = self.order_line.filtered(lambda x: x.product_id == line.product_id and x.free_products == True)
                                if pol:
                                    for p in pol:
                                        p.product_qty = qty
                                else:
                                    self.update({
                                        'order_line':[(0,0,{
                                            'free_products': True,
                                            'product_id': line.product_id.id,
                                             'name': line.product_id.name,
                                            'date_planned':line.date_planned,
                                            'product_uom':line.product_id.uom_po_id.id,
                                            'price_unit':price_unit,
                                           'product_qty': qty,
                                            'father_line': line.id,
                                        })]
                                    })
                            else:
                                pol = self.order_line.filtered(lambda x: x.product_id == line.product_id and x.free_products == True)
                                if pol:
                                    for p in pol:
                                        p.product_qty = qty

                    if d.apply_type == 'discount_products':
                        amount = (d.discount/100)*line.price_subtotal
                        self.amount_purchase = self.amount_purchase + amount
                    if add not in promotions and d.apply_type not in ['invoice','credit_note','ant_inv']:
                        promotions.append(add)
            line.price_unit = price_unit
       
        self.promotion_ids = promotions
        self.promotion_ap_ids = promotions_ap
        
    @api.onchange('partner_id')
    def oncange_promotion_ap_ids(self):        
        if self.partner_id:
            self.promotion_ap_ids = False
            today = date.today()
            promotions = self.env['ludi.product.promotion'].search([
                ('partner_id','=',self.partner_id.id),
                '|',('date_begin','>=',today),('date_begin','=',False),
                '|',('date_end','<=',today),('date_end','=',False),
                ('in_purchase','=',False)
            ])
            if promotions:
                self.promotion_ap_ids = [(6, 0, promotions.ids)]
    
    def copy(self):
        res = super(LudiPurchaseOrder).copy()
        for line in res.order_line:
            line.onchange_values_product()
        res.onchange_order_line_value()
        return res
    

    def picking_no_delivery(self,partner_id,date):
        picking = self.env['stock.picking'].search([
            ('partner_id','=',partner_id),
            ('free_products','=',True),
            ('state','not in',['done','cancel']),
            ('picking_type_code','=','incoming'),
            ('scheduled_date','<',date)
        ])
        if picking:
            return False
        else:
            return True
        
    def button_confirm(self):
        res = super(LudiPurchaseOrder, self).button_confirm()
        result = self.picking_no_delivery(self.partner_id.id,datetime.now())
        if result == False:
            raise ValidationError(('No puede completar la creación de esta compra, existen mercancías que aún no han sido entregadas'))
        else:
            return res
    
    
    