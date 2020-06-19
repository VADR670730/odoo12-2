# -*- coding: utf-8 -*-
{
    "name": "销售折扣",
    "version": "0.1",
    "summary": """Sale Order Amount Extend""",
    "description": """添加四种折扣 TD PD IO OT""",
    "author": "Michaelwolf Wang",
    "depends": ["base","sale","account"],
    'sequence': 1,
    "data": [
             'view/res_partner_view.xml',
             'view/sale_order_view.xml',
             'view/account_invoice_view.xml',
    ],
    'images' : [],
    'demo': [
    ],
    'qweb': [
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
