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


class res_partner(models.Model):
    _inherit = 'res.partner'

    @api.one
    def _inverse_product_pricelist(self):
        pls = self.env['product.pricelist'].search(
            [('country_group_ids.country_ids.code', '=', self.country_id and self.country_id.code or False)],
            limit=1
        )
        default_for_country = pls and pls[0]
        actual = self.env['ir.property'].get('property_product_pricelist', 'res.partner', 'res.partner,%s' % self.id)

        # update at each change country, and so erase old pricelist
        if self.property_product_pricelist or (actual and default_for_country and default_for_country.id != actual.id):
            self.env['ir.property'].sudo().set_multi(
                'property_product_pricelist',
                self._name,
                {self.id: self.property_product_pricelist or default_for_country.id},
                default_value=default_for_country.id
            )
        self.property_product_pricelist2=self.env['product.pricelist']._get_partner_pricelist(self.id)

    partner_product_ids = fields.One2many('res.partner.product', 'partner_id', u'客户产品编码表', )
    property_product_pricelist1 = fields.Many2one('product.pricelist', u'零售价格表')
    property_product_pricelist2 = fields.Many2one('product.pricelist',u'供货价')
    property_product_pricelist3 = fields.Many2one('product.pricelist', u'结算价格表')
    not_show_in_product_pricelist= fields.Boolean(u'去掉价格表查询', default=False)

    test_ids = fields.One2many('res.partner.test', 'master_id', u'拜访记录')

    @api.onchange('property_product_pricelist')
    def _onchange_property_product_pricelist(self):
        if self.property_product_pricelist:
           self.property_product_pricelist2=self.property_product_pricelist.id
        else:
            self.property_product_pricelist2=False


    @api.multi
    def action_update_property_product_pricelist2(self):
        objs=self.search([('customer','=',True)])
        for x in objs:
            if x.property_product_pricelist and not x.property_product_pricelist2:
               x.property_product_pricelist2=x.property_product_pricelist.id



class res_partner_test(models.Model):
    _name = 'res.partner.test'
    _description = u''

    master_id = fields.Many2one('res.partner', u'业半')
    partner_id = fields.Many2one('res.partner', u'联系人')
