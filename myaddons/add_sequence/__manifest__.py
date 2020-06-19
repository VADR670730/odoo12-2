# -*- coding: utf-8 -*-
{
    'name': "add_sequence",

    'summary': """
        订单明细行添加序号显示
        """,

    'description': """
        销售订单行，采购订单行，调拨单明细行，添加了产品序号显示
    """,

    'author': "404nF",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    # 'depends': ['base','sale','purchase','mrp','product','stock','sale_stock'],
    'depends': ['base','sale','purchase','mrp','product','stock','sale_stock'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}