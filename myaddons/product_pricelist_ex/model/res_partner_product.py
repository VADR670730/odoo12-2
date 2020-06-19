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


class res_partner_product(models.Model):
    _name = 'res.partner.product'
    _description = u'客户产品编码表'

    @api.multi
    @api.depends('name', 'code')
    def name_get(self):
        res = []
        for r in self:
            name = "%s-%s" % (r.code, r.name)
            res.append((r.id, name))
        return res

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        # recs = self.browse()
        recs = self.env['res.partner.product']
        if name:
            recs = self.search(
                ['|',('name', operator, name),('code', 'like', name)],limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()

    partner_id = fields.Many2one('res.partner', u'客户', required=True, domain=[('customer', '=', True)])
    product_id = fields.Many2one('product.product', u'我司产品', required=True)
    code = fields.Char(u'客户产品编码', required=True)
    name = fields.Char(u'客户产品名称', required=True)
    note = fields.Text(u'备注')
    active = fields.Boolean(u'启用', default=True)

    _sql_constraints = [('unique_name', 'unique (partner_id,name)', u'客户产品名称 不可重复!'),
                        ('unique_code', 'unique (partner_id,code)', u'客户产品编码 不可重复!'),
                        ('unique_product_id', 'unique (partner_id,product_id)', u'客户对应我司产品 不可重复!'),]

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
