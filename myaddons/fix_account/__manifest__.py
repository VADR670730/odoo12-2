# -*- coding: utf-8 -*-
{
    'name': "完善过账差异",
    'sequence': 1,
    'application': True,

    'summary': """
        付款差异下的过账差额可多选并生成多张日记账
        收付款不同币种与本位币之间实现手工汇率转换""",

    'description': """
        Long description of module's purpose
    """,

    'author': "zoro",
    'website': "http://www.yourcompany.com",

    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'account_reports'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'wizard/change_invoice_amount_wizard.xml',
        'views/account_payment_view.xml',

    ],
    # only loaded in demonstration mode
    'demo': [

    ],
}
