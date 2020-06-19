# -*- coding: utf-8 -*-
{
    'name': "stock_checked",
    'sequence': 1,
    'application': True,

    'summary': """
        1 库存的工作流中添加已检查
        2 产品的导出新增产品条码名称拼接字段
        """,

    'description': """
        Long description of module's purpose
    """,

    'author': "zoro",
    'website': "http://www.yourcompany.com",

    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'stock', 'product'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/stock_checked.xml',

    ],
    # only loaded in demonstration mode
    'demo': [

    ],
}
