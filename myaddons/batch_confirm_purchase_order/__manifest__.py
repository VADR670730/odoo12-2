# -*- coding: utf-8 -*-
{
    'name': "batch_confirm_purchase_order",

    'summary': """添加批量确认采购订单""",

    'description': """
        通过服务器动作添加批量确采购订单""",

    'author': "404nF",
    'website': "http://www.megacombine.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','purchase'],

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