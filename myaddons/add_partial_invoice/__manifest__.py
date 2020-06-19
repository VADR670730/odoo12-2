# -*- coding: utf-8 -*-
{
    'name': "add_partial_invoice",

    'summary': """
        添加销售和采购部分开票功能
        """,

    'description': """
        Long description of module's purpose
    """,

    'author': "zoro",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'sale_management', 'sale', 'purchase'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        # 'views/views.xml',
        # 'wizard/add_partial_inv_wizard.xml',
        'views/recom_entire_invoice.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}