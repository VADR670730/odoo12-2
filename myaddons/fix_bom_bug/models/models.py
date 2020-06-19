# -*- coding: utf-8 -*-

from odoo import models, fields, api


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'
    
    # @api.onchange('parent_product_tmpl_id')
    # def onchange_parent_product(self):
    #     if not self.parent_product_tmpl_id:
    #         return {}
    #     return {'domain': {'attribute_value_ids': [
    #         ('id', 'in', self.parent_product_tmpl_id._get_valid_product_attribute_values().ids),
    #         ('attribute_id.create_variant', '!=', 'no_variant')
    #     ]}}

    @api.onchange('parent_product_tmpl_id')
    def onchange_parent_product(self):
        return {'domain': {'attribute_value_ids': [
            ('id', 'in', self.parent_product_tmpl_id.mapped('attribute_line_ids.value_ids.id')),
            ('attribute_id.create_variant', '!=', 'no_variant')
        ]}}


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.multi
    def _get_valid_product_attribute_values(self):
        """deprecated, use `valid_product_attribute_value_ids`"""
        self.ensure_one()
        return self.valid_product_attribute_value_ids
