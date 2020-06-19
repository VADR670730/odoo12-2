# -*- coding: utf-8 -*-
{
    'name': "alter_invocice_deliver_sale_purchase_report",

    'summary': """修改报表""",

    'description': """
        修改发票，送货单，销售订单，采购订单报表
    """,

    'author': "404nF",
    'website': "http://www.megacombine.com/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','stock','account','web','sale','purchase'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'views/views.xml',
        # 'views/templates.xml',
        'report/external_layout_background_inherit.xml',
        'report/account_report_invoice_with_payments_inherit.xml',
        'report/stock_report_deliveryslip_inherit.xml',
        'report/sale_quotation_report_inherit.xml',
        'report/purchase_quotation_report_inherit.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
