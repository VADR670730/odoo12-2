# -*- encoding: utf-8 -*-
import time, datetime
from collections import defaultdict, OrderedDict
from operator import itemgetter
from itertools import groupby
import math
from odoo import models, fields, api, _, tools, SUPERUSER_ID
import odoo.addons.decimal_precision as dp
from odoo.tools import float_compare, float_round, float_is_zero
from odoo.exceptions import UserError, ValidationError


class product_pricelist_list(models.Model):
    _name = 'product.pricelist.list'
    _log_access = False
    _description = u'产品价格表查询'

    pricelist_id = fields.Many2one('product.pricelist', u'价格表')
    currency_id = fields.Many2one('res.currency', 'Currency')
    product_id = fields.Many2one('product.product', u'我司产品')
    price = fields.Float(u'单价')
    date_start = fields.Date(u'时间起')
    date_end = fields.Date(u'时间止')
    company_id = fields.Many2one('res.company', u'公司')
    note = fields.Text(u'备注')
