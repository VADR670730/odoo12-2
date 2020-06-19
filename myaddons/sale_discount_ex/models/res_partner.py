# -*- coding: utf-8 -*-
from odoo import models, fields, api
import odoo.addons.decimal_precision as dp


class res_partner(models.Model):
    _inherit = 'res.partner'
    _description = u'Partner'

    discount_td = fields.Float(u'TD%', digits=dp.get_precision('Discount'))
    discount_pd = fields.Float(u'PD%', digits=dp.get_precision('Discount'))
    discount_io = fields.Float(u'IO%', digits=dp.get_precision('Discount'))
    discount_ot = fields.Float(u'OT%', digits=dp.get_precision('Discount'))
    x_guest_supplier_code = fields.Char('Guest Code', help='客户方对供应商（我司）的编码')