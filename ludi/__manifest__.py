# -*- coding: utf-8 -*-
{
    'name': "Ludi",

    'summary': """
        New features Odoo""",

    'description': """
        Inherit some views , new views , reports
    """,

    'author': "Estrasol -Arturo Jasso",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base','product','sale','purchase','calendar','point_of_sale','stock',
        'account','product_expiry','sale_margin','crm',
    ],

    # always loaded
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        #cron
        'cron/cron.xml',
        #mail
        'data/temporality.xml',
        'data/produc_recipt.xml',
        'data/purchase_write.xml',
        #report
        'report/report_delivery_inherit.xml',
        'report/report_purchase_inherit.xml',
        #Views
        'views/product/product.xml',
        'views/product/product_product.xml',
        'views/res_user/res_user.xml',
        'views/temporality/temporality.xml',
        'views/purchase/purchase_order.xml',
        'views/stock/stock_picking.xml',
        'views/pos/pos_config.xml',
        'views/stock/stock_quant.xml',
        'views/contacts/res_partner.xml',
        'views/product_promotion/product_promotion.xml',
        'views/calendar/calendar.xml',
        'views/stock/stock_location.xml',
        'views/brand/brand.xml',
        'views/stock/stock_move_line.xml',
        'views/sale/sale_order.xml',
        'views/pricelist/product_pricelist_item.xml',
        #wizard
        'wizard/open_calendar_view.xml',
        'wizard/free_products.xml',
        #mail
        'mail/client_alert.xml',
        #menu
        'views/menu.xml',
    ],  
     'qweb': [
        
         ]
        ,
    'demo': [
    ],
    'application': True,
}
