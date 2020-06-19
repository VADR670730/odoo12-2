# -*- coding: utf-8 -*-
{
    'name': "fix_stock_report",

    'summary': """
        分拣单打印格式修改""",

    'description': """
        Long description of module's purpose
    """,

    'author': "zoro",
    'website': "http://www.yourcompany.com",

    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'stock'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/stock_templates.xml',
        'report/stock.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}