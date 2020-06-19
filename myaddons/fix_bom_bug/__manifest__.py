# -*- coding: utf-8 -*-
{
    'name': "fix_bom_bug",

    'summary': """
        修复物料清单bug
        """,

    'description': """
        物料清单创建，添加产品明细行报错
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
    'depends': ['base','mrp','product'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}