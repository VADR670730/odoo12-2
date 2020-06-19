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


class update_partner_product_wizard(models.Model):
    _name = 'update.partner.product.wizard'
    _description = u'更新数据到价格表'

    @api.multi
    def action_update_all_pricelist(self):
        sql = """
               update product_pricelist_item a set partner_product_id=c.id
                 from product_pricelist b ,res_partner_product c
                where a.pricelist_id=b.id
                  and a.product_id=c.product_id
                  and c.partner_id=b.partner_id
                  and c.id is not null;
        """
        self._cr.execute(sql)

