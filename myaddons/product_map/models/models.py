# -*- coding: utf-8 -*-

from odoo import models, fields, api

from odoo.exceptions import ValidationError
from odoo.osv import expression
import re

class ProductMap(models.Model):

    _name = "product.map"

    name = fields.Char(readonly=True, related='partner_id.name', copy=False)
    partner_id = fields.Many2one('res.partner',string="客户", domain=[["customer", "=", True]])
    sub_id = fields.One2many('product.map.line', 'parent_id', string="产品映射子表")

    @api.constrains('partner_id')
    def _check_partner_unique(self):
        for order in self:
            partner_id = order.partner_id
            count = order.search_count([["partner_id","=",partner_id.id]])
            if count > 1:
                raise ValidationError("对应客户映射已存在")


class ProductMapLine(models.Model):

    _name = 'product.map.line'

    _rec_name = 'map_product'

    parent_id = fields.Many2one("product.map", string='产品映射父表')
    partner_id = fields.Many2one('res.partner', string='客户',related='parent_id.partner_id',store=True)
    product_id = fields.Many2one('product.product', string='我司产品', required = True)
    product_barcode = fields.Char(string='产品条码',related = 'product_id.barcode')
    map_product = fields.Char(string='客户产品名称',required = True)
    map_product_barcode = fields.Char(string='客户产品编码',required = True)
    # sale_line = fields.One2many('sale.order.line','map_product_line',string='销售订单行')

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        if not args:
            args = []
        if name:
            positive_operators = ['=', 'ilike', '=ilike', 'like', '=like']
            product_ids = []
            if operator in positive_operators:
                # 先搜客户自己产品的编码
                product_ids = self._search([('product_id.barcode', '=', name)] + args, limit=limit,
                                           access_rights_uid=name_get_uid)
                # if not product_ids:
                    # 没有再搜客我司的条码
                    # product_id = self.env['product.product']._search([['barcode','=',name]])
                    # product_ids = self._search([('product_id', '=', product_id)] + args, limit=limit, access_rights_uid=name_get_uid)
            if not product_ids and operator not in expression.NEGATIVE_TERM_OPERATORS:
                # Do not merge the 2 next lines into one single search, SQL search performance would be abysmal
                # on a database with thousands of matching products, due to the huge merge+unique needed for the
                # OR operator (and given the fact that the 'name' lookup results come from the ir.translation table
                # Performing a quick memory merge of ids in Python will give much better performance
                # product_ids = self._search([('map_product_barcode', '=', name)] + args, limit=limit, access_rights_uid=name_get_uid)

                product_ids = self._search(args + [('map_product_barcode', operator, name)], limit=limit)
                if not limit or len(product_ids) < limit:
                    # we may underrun the limit because of dupes in the results, that's fine
                    limit2 = (limit - len(product_ids)) if limit else False
                    product2_ids = self._search(args + [('map_product', operator, name), ('id', 'not in', product_ids)], limit=limit2, access_rights_uid=name_get_uid)
                    product_ids.extend(product2_ids)

                # product_ids = self._search([('map_product', operator, name)] + args, limit=limit, access_rights_uid=name_get_uid)
            elif not product_ids and operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = expression.OR([
                    ['&', ('map_product_barcode', operator, name), ('map_product', operator, name)],
                    ['&', ('map_product_barcode', '=', False), ('map_product', operator, name)],
                ])
                domain = expression.AND([args, domain])
                product_ids = self._search(domain, limit=limit, access_rights_uid=name_get_uid)
            if not product_ids and operator in positive_operators:
                ptrn = re.compile('(\[(.*?)\])')
                res = ptrn.search(name)
                if res:
                    product_ids = self._search([('map_product_barcode', '=', res.group(2))] + args, limit=limit, access_rights_uid=name_get_uid)
        else:
            product_ids = self._search(args, limit=limit, access_rights_uid=name_get_uid)
        return self.browse(product_ids).name_get()

    @api.multi
    def name_get(self):
        result = []

        for map_product in self:
            map_product_tuple = (map_product.id,"[%s] %s"% (map_product.map_product_barcode,map_product.map_product))
            result.append(map_product_tuple)

        return result

    @api.constrains('product_id')
    def _check_product_unique(self):

        for line in self:
            product_id = line.product_id
            parent_id = line.parent_id
            count = line.search_count([["product_id","=",product_id.id],["parent_id",'=',parent_id.id]])

            if count > 1:
                raise ValidationError("对应产品映射已存在")

    # @api.constrains('product_id')
    # def _check_product_unique(self):
    #     product_id = self.product_id
    #     parent_id = self.parent_id
    #     count = self.search_count([["product_id","=",product_id.id],["parent_id",'=',parent_id.id]])
    #     if count > 1:
    #         raise ValidationError("对应产品映射已存在")

    @api.constrains("map_product")
    def _check_map_product_name(self):
        for line in self:
            map_product = line.map_product
            parent_id = line.parent_id
            count = line.search_count([["map_product", "=", map_product], ["parent_id", '=', parent_id.id]])
            if count > 1:
                raise ValidationError("客户产品名称已存在")

    # @api.constrains("map_product")
    # def _check_map_product_name(self):
    #     map_product = self.map_product
    #     parent_id = self.parent_id
    #     count = self.search_count([["map_product", "=", map_product], ["parent_id", '=', parent_id.id]])
    #     if count > 1:
    #         raise ValidationError("客户产品名称已存在")

    @api.constrains("map_product_barcode")
    def _check_map_product_barcode(self):
        for line in self:
            map_product_barcode = line.map_product_barcode
            parent_id = line.parent_id
            count = line.search_count([["map_product_barcode", "=", map_product_barcode], ["parent_id", '=', parent_id.id]])
            if count > 1:
                raise ValidationError("客户产品编码已存在")

    # @api.constrains("map_product_barcode")
    # def _check_map_product_barcode(self):
    #     map_product_barcode = self.map_product_barcode
    #     parent_id = self.parent_id
    #     count = self.search_count([["map_product_barcode", "=", map_product_barcode], ["parent_id", '=', parent_id.id]])
    #     if count > 1:
    #         raise ValidationError("客户产品编码已存在")


class Partner(models.Model):
    _inherit = 'res.partner'
    map_line = fields.One2many('product.map.line','partner_id',string='客户的映射产品')


class ProductProduct(models.Model):
    _inherit = "product.product"
    map_line = fields.One2many('product.map.line', "product_id", string='产品映射')


class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    # map_product_line = fields.Many2one('product.map.line',string='客户产品',domain=lambda self: [('partner_id', '=', self.order_id.partner_id.id)])
    map_product_line = fields.Many2one('product.map.line',string='客户产品')
    map_product_barcode = fields.Char(related = 'map_product_line.map_product_barcode',string='客户产品条码')

    @api.onchange('map_product_line','product_id')
    def _onchange_map_product_line(self):
        flag_map_product = self._context.get("product_id",False)
        flag_product = self._context.get("map_product_line",False)
        partner_id = self._context.get("partner_id",False)

        if not partner_id:
            raise ValidationError("请先选择客户!!!")

        if flag_product:
            product_id = self.product_id
            self.map_product_line = product_id.map_line.filtered(lambda line:line.partner_id.id == partner_id)
            # map_product_line = self.env['product.map.line'].search(
            #     [['partner_id','=',partner_id],['product_id','=',product_id.id]])
            # self.map_product_line = map_product_line
        elif flag_map_product:
            self.product_id = self.map_product_line.product_id
        else:
            map_product_line = self.map_product_line
            product_id = self.product_id
            if map_product_line and not product_id:
                self.product_id = map_product_line.product_id
            elif product_id and not map_product_line:
                self.map_product_line = product_id.map_line.filtered(lambda line: line.partner_id.id == partner_id)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    sub_nums = fields.Integer(string="销售订单明细行数量", compute='_compute_sub_nums')


    @api.multi
    def onchange(self, values, field_name, field_onchange):
        res = super().onchange(values,field_name,field_onchange)
        return res


    @api.onchange('order_line')
    def _compute_sub_nums(self):
        nums = len(self.order_line)
        self.sub_nums = nums

    @api.onchange('partner_id')
    def onchange_order_line(self):
        order_lines = self.order_line
        partner_id = self.partner_id
        if self.partner_id != self.partner_shipping_id:
            for line in order_lines:
                product_id = line.product_id
                map_product = product_id.map_line.filtered(lambda line:line.partner_id == partner_id)
                line.map_product_line = map_product




# res = [(5,), (1, 102,
#               {'name': '[00006] 闺艾朗-日用卫生巾（18片-25cm）', 'sequence': 10, 'invoice_lines': [(5,)], 'invoice_status': 'no',
#                'price_unit': 1.0, 'price_subtotal': 0.86, 'price_total': 1.0, 'tax_id': [(5,), (4, 1)], 'discount': 0.0,
#                'product_id': (85, '[00006] 闺艾朗-日用卫生巾（18片-25cm）'), 'product_updatable': True, 'product_uom_qty': 1.0,
#                'product_uom': (1, 'Unit(s)'), 'product_custom_attribute_value_ids': [(5,)],
#                'product_no_variant_attribute_value_ids': [(5,)], 'qty_delivered': 0.0, 'qty_delivered_manual': 0.0,
#                'qty_to_invoice': 0.0, 'qty_invoiced': 0.0, 'currency_id': (7, 'CNY'), 'analytic_tag_ids': [(5,)],
#                'state': 'draft', 'customer_lead': 0.0, 'display_type': False, 'qty_delivered_method': 'stock_move',
#                'product_packaging': False, 'route_id': False, 'barcode': '8809016360267', 'show_sequence': 1,
#                'map_product_line': (2, '闺艾朗-日用卫生巾dsfdsf'), 'partner_id': (65, '客户')})]
