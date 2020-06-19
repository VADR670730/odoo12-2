# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    code_name = fields.Char(string='产品条码名称拼接', compute='_compute_code_name')

    @api.one
    @api.depends('name', 'barcode', 'default_code')
    def _compute_code_name(self):
        self.code_name = '[' + str(self.barcode) + ']' + '[' + str(self.default_code) + ']' + ' ' + str(self.name)
