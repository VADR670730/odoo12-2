# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# Copyright (C) 2008-2008 Michaelwolf   michaelwolf_wang@126.com <extend product pricelist>
# QQ: 3472317647
{
    "name": "价格表功能扩",
    "version": "1.0",
    "summary": """
    价格表功能扩:每个客户增加 三个价格表1.零售价
                                     2.供货价
                                     3.结算价
    """,
    "description": """
    模组说明:

    """,
    "menus_by_module": """
        *1.客产品编码表
        *2.客产品编码表及价格
    """,
    "category": "Product",
    "author": "michaelwolf wang",
    "website": "",
    "depends": ['base','product','sale'],
    "data": [
        'security/ir.model.access.csv',

        'views/res_partner_product_view.xml',
        'views/product_pricelist_view.xml',
        'views/product_pricelist_list_view.xml',
        'views/sale_order_view.xml',
        'views/res_partner_view.xml',
        'views/partner_product_pricelist_view.xml',

        # 'wizard/update_partner_product_wizard_view.xml',


    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
