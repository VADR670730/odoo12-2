# -*- coding:utf-8 -*-
# """销售模块扩展"""
from odoo import fields, models, api, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import ValidationError, UserError
from odoo.tools import float_is_zero

MAP_INVOICE_TYPE_PAYMENT_SIGN = {
    'out_invoice': 1,
    'in_refund': -1,
    'in_invoice': -1,
    'out_refund': 1,
}

MAP_INVOICE_TYPE_PARTNER_TYPE = {
    'out_invoice': 'customer',
    'out_refund': 'customer',
    'in_invoice': 'supplier',
    'in_refund': 'supplier',
}


# 销售订单明细行添加销售单位，销售单位数量，销售单位转换率，重写订购数量与小计方法
class SaleOrderLines(models.Model):
    _inherit = 'sale.order.line'

    product_sale_unit = fields.Many2one('uom.uom', string='销售单位')

    price_items_id = fields.Many2one('product.pricelist.item')

    product_sale_num = fields.Float(string='销售数量', digits=dp.get_precision('Product Unit of Measure'),
                                    required=True, default=1.0)
    product_unit_conversion = fields.Float(string='销售单位转换率', default='1.0')

    price_subtotal = fields.Monetary(compute='_compute_amount', string='小计', readonly=True, store=True)

    product_uom = fields.Many2one('uom.uom', string='Unit of Measure', readonly=True)

    product_uom_qty = fields.Float(string='订购数量', digits=dp.get_precision('Product Unit of Measure'),
                                   required=True, default=1.0, store=True)

    # 根据销售单位数量自动计算订购数量
    @api.onchange('product_id', 'product_sale_num', 'product_unit_conversion')
    def _compute_order_number(self):
        for line in self:
            line.product_uom_qty = line.product_unit_conversion * line.product_sale_num

    # 根据订购数量自动计算销售单位数量
    @api.onchange('product_id', 'product_uom_qty', 'product_unit_conversion')
    def _compute_product_uom_num(self):
        for line in self:
            if line.product_unit_conversion == 0:
                # line.product_sale_unit = line.product_uom
                break
            line.product_sale_num = line.product_uom_qty / line.product_unit_conversion

    # 判断所输入的订购数量是否与所选择的计量单位相符合
    @api.onchange('product_uom_qty')
    def judge_unit_uom(self):
        for line in self:
            result = line.product_sale_num
            result1 = int(result)
            if result != result1:
                raise ValidationError('您输入的订购数量与所选择的销售单位不符')

    # 计量单位，单位数量改变时改变传入的价格参数
    @api.onchange('product_uom_qty', 'product_sale_unit')
    def product_uom_change(self):
        product_list = []
        env_price = self.order_id.pricelist_id.item_ids
        for product in env_price:
            product_list.append(product.product_tmpl_id.name)
        if not self.product_sale_unit or not self.product_id:
            self.price_unit = 0.0
            return
        if self.order_id.pricelist_id and self.order_id.partner_id:
            product = self.product_id.with_context(
                lang=self.order_id.partner_id.lang,
                partner=self.order_id.partner_id,
                quantity=self.product_sale_num,
                date=self.order_id.date_order,
                pricelist=self.order_id.pricelist_id.id,
                uom=self.product_uom.id,
                fiscal_position=self.env.context.get('fiscal_position'),
                sale_uom=self.product_sale_unit.name,
                # sale_nums=self.product_sale_num
            )

            self.price_unit = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product),
                                                                                      product.taxes_id, self.tax_id,
                                                                                      self.company_id)

    # 当选择产品时，自动根据价格表中所符合的计量单位选择对应的价格
    @api.onchange('product_id')
    def _select_measuring_unit(self):
        product_list = []
        env_price = self.order_id.pricelist_id.item_ids
        pricelist_env = self.order_id.pricelist_id

        for product in env_price:
            product_list.append(product.product_tmpl_id.name)
        for line in self:
            if line.product_id.name == False:
                break

            for item in pricelist_env.item_ids:
                if line.product_id.name == item.product_tmpl_id.name:
                    if line.product_sale_num >= item.min_quantity:
                        line.product_unit_conversion = item.product_measuring_unit.factor_inv
                        line.product_sale_unit = item.product_measuring_unit
                        break

                else:
                    line.product_sale_unit = line.product_uom
                    line.product_unit_conversion = line.product_uom.factor_inv
            #
            # if line.product_id.name in product_list:
            #     pass
            # else:
            #     if pricelist_env.id == 1:
            #         pass
            #     else:
            #         return {
            #
            #             'warning': {
            #                 'title': "提示",
            #                 'message': "您选择价格表没有这个产品",
            #             }
            #         }

    # 判断所选择的销售单位是否存在所选择的价格表中
    @api.onchange('product_sale_unit')
    def price_unit_by_uom(self):
        list1 = []
        list2 = []
        env_price = self.order_id.pricelist_id.item_ids

        for line in self:
            if line.product_id.name == False:
                break
            line.product_unit_conversion = line.product_sale_unit.factor_inv

        for line in env_price:
            list1.append(line.product_measuring_unit_name)

        for product in env_price:
            list2.append(product.product_tmpl_id.name)

        for item in self:
            if item.product_id.name == False:
                break
            if item.product_id.name not in list2:
                break
            product_env = self.env['product.pricelist.item'].search([('product_tmpl_id', '=', item.product_id.id), (
                'product_measuring_unit_name', '=', item.product_sale_unit.name), ('pricelist_id', '=',
                                                                                   item.order_id.pricelist_id.id)])
            # if product_env:
            #     pass
            # else:
            #     if item.product_uom.name == item.product_sale_unit.name:
            #         break
            #
            #     raise ValidationError('此销售单位在该产品的价格表中不存在')

    # 判断最小数量与订购数量，然后得出对应的价格
    @api.onchange('product_id')
    def judge_min_quantity(self):
        list2 = []

        env_price = self.order_id.pricelist_id.item_ids
        for product in env_price:
            if self.product_id.name == False:
                break
            if self.product_id.name == product.product_tmpl_id.name:
                list2.append(product.min_quantity)
        list3 = sorted(list2)

        if list3 != []:
            if self.product_uom_qty < list3[0]:
                self.product_sale_unit = self.product_uom
                self.product_unit_conversion = self.product_uom.factor_inv

    # 改变传入的参数，实现价格的计算
    @api.onchange('product_id', 'price_unit', 'product_uom', 'product_uom_qty', 'tax_id')
    def _onchange_discount(self):
        if not (self.product_id and self.product_uom and
                self.order_id.partner_id and self.order_id.pricelist_id and
                self.order_id.pricelist_id.discount_policy == 'without_discount' and
                self.env.user.has_group('sale.group_discount_per_so_line')):
            return

        self.discount = 0.0
        product = self.product_id.with_context(
            lang=self.order_id.partner_id.lang,
            partner=self.order_id.partner_id,
            quantity=self.product_sale_num,
            date=self.order_id.date_order,
            pricelist=self.order_id.pricelist_id.id,
            uom=self.product_uom.id,
            fiscal_position=self.env.context.get('fiscal_position')
        )

        product_context = dict(self.env.context, partner_id=self.order_id.partner_id.id, date=self.order_id.date_order,
                               uom=self.product_uom.id)

        price, rule_id = self.order_id.pricelist_id.with_context(product_context).get_product_price_rule(
            self.product_id, self.product_uom_qty or 1.0, self.order_id.partner_id)
        new_list_price, currency = self.with_context(product_context)._get_real_price_currency(product, rule_id,
                                                                                               self.product_uom_qty,
                                                                                               self.product_uom,
                                                                                               self.order_id.pricelist_id.id)

        if new_list_price != 0:
            if self.order_id.pricelist_id.currency_id != currency:
                # we need new_list_price in the same currency as price, which is in the SO's pricelist's currency
                new_list_price = currency._convert(
                    new_list_price, self.order_id.pricelist_id.currency_id,
                    self.order_id.company_id, self.order_id.date_order or fields.Date.today())
            discount = (new_list_price - price) / new_list_price * 100
            if discount > 0:
                self.discount = discount

    # 改变传入的参数，实现价格的计算
    @api.depends('product_id', 'product_sale_num', 'discount', 'tax_id', 'product_uom_qty')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            # result = line.product_sale_num
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_sale_num,
                                            product=line.product_id, partner=line.order_id.partner_shipping_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    # 改变传入的参数，实现发票明细行的计算
    @api.multi
    def _prepare_invoice_line(self, qty):
        """
        Prepare the dict of values to create the new invoice line for a sales order line.

        :param qty: float quantity to invoice
        """
        self.ensure_one()
        res = {}
        account = self.product_id.property_account_income_id or self.product_id.categ_id.property_account_income_categ_id

        if not account and self.product_id:
            raise UserError(
                _('Please define income account for this product: "%s" (id:%d) - or for its category: "%s".') %
                (self.product_id.name, self.product_id.id, self.product_id.categ_id.name))

        fpos = self.order_id.fiscal_position_id or self.order_id.partner_id.property_account_position_id
        if fpos and account:
            account = fpos.map_account(account)

        res = {
            'name': self.name,
            'sequence': self.sequence,
            'origin': self.order_id.name,
            'account_id': account.id,
            'price_unit': self.price_unit,
            'quantity': qty / self.product_sale_unit.factor_inv,
            # 'product_sale_num': self.product_sale_num,
            'discount': self.discount,
            'uom_id': self.product_sale_unit.id,
            'product_id': self.product_id.id or False,
            'invoice_line_tax_ids': [(6, 0, self.tax_id.ids)],
            'account_analytic_id': self.order_id.analytic_account_id.id,
            'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
            'display_type': self.display_type,
        }
        return res


# 交货单添加销售单位，销售单位数量
class StockPickings(models.Model):
    _inherit = 'stock.move'

    product_unit = fields.Many2one('uom.uom', string='销售单位', readonly=True)

    product_unit_num = fields.Float(string='销售数量', compute='_compute_product_unit_num', required=True, default=1.0,
                                    readonly=False, digits=dp.get_precision('Product Unit of Measure'))

    # product_sale_num = fields.Float(string='订单参考数量')

    # 实现交货单中销售单位数量与销售单位之间的对应关系
    @api.multi
    def _compute_product_unit_num(self):

        for line in self:
            if '退回' not in str(line.picking_id.origin):
                if line.picking_id.picking_type_id.name != '交货单':
                    return
                # uom_env = self.env['uom.uom'].search([('name', '=', line.product_unit)])
                try:
                    line.product_unit_num = line.product_uom_qty / line.product_unit.factor_inv
                except:
                    pass


# 价格表添加计量单位字段
class SaleOrderPrice(models.Model):
    _inherit = "product.pricelist.item"

    product_measuring_unit = fields.Many2one('uom.uom', string='计量单位', store=True)

    product_measuring_unit_name = fields.Char(string='计量单位', readonly=True, related='product_measuring_unit.name',
                                              store=True)

    sale_order_line_ids = fields.One2many('sale.order.line', 'price_items_id')

    product_sale_uom = fields.Char(string='计量单位', related='product_measuring_unit.name')

    applied_on = fields.Selection([
        ('3_global', 'Global'),
        ('2_product_category', ' Product Category'),
        ('1_product', 'Product'),
        ('0_product_variant', 'Product Variant')], "Apply On",
        default='3_global', required=True,
        help='Pricelist Item applicable on selected option')

    # 根据应用场景的不同实现计量单位的选择
    @api.onchange('applied_on', 'product_tmpl_id', 'product_id')
    def _compute_product_measuring_unit(self):
        if self.applied_on == '1_product':
            self.product_measuring_unit = self.product_tmpl_id.uom_id
        elif self.applied_on == '0_product_variant':
            self.product_measuring_unit = self.product_id.uom_id
        else:
            self.product_measuring_unit = False

    # 实现在价格表中添加产品时计量单位可以实时显示在价格表明细行中
    @api.onchange('product_measuring_unit')
    def _compute_unit_name(self):
        if self.product_sale_uom == False:
            return 0
        self.product_sale_uom = self.product_measuring_unit.name


# 给价格表明细行添加产品时增加约束
# @api.one
# @api.constrains('product_tmpl_id', 'min_quantity', 'product_sale_uom', 'date_start', 'date_end')
# def judge_have_same_price(self):
#     count = 0
#     dict1 = {}
#     product_list = []
#     product_list2 = []
#
#     for line in self:
#         dict1['product_name'] = line.product_tmpl_id.name
#         dict1['min_quantity'] = line.min_quantity
#         dict1['product_sale_uom'] = line.product_sale_uom
#         dict1['date_start'] = line.date_start
#         dict1['date_end'] = line.date_end
#         product_list2.append(dict1)
#
#     for item in self.pricelist_id.item_ids:
#         dict2 = {}
#         dict2['product_name'] = item.product_tmpl_id.name
#         dict2['min_quantity'] = item.min_quantity
#         dict2['product_sale_uom'] = item.product_sale_uom
#         dict2['date_start'] = item.date_start
#         dict2['date_end'] = item.date_end
#         product_list.append(dict2)
#
#     for product1 in product_list2:
#         if product1['date_start'] and product1['date_end']:
#             for product in product_list:
#                 if product1['product_name'] == product['product_name'] and product1['min_quantity'] == product[
#                     'min_quantity'] and product1['product_sale_uom'] == product['product_sale_uom']:
#                     if product['date_start'] and product['date_end']:
#                         if product1['date_start'] <= product['date_end'] and product1['date_end'] >= product[
#                             'date_start']:
#                             count += 1
#                     elif product['date_start'] == False and product['date_end'] == False:
#                         count += 1
#                     elif product['date_start'] and product['date_end'] == False:
#                         if product1['date_end'] >= product['date_start']:
#                             count += 1
#                     else:
#                         if product1['date_start'] <= product['date_end']:
#                             count += 1
#
#         elif product1['date_start'] == False and product1['date_end'] == False:
#             for product in product_list:
#                 if product1['product_name'] == product['product_name'] and product1['min_quantity'] == product[
#                     'min_quantity'] and product1['product_sale_uom'] == product['product_sale_uom']:
#                     count += 1
#
#         elif product1['date_start'] and product1['date_end'] == False:
#             for product in product_list:
#                 if product1['product_name'] == product['product_name'] and product1['min_quantity'] == product[
#                     'min_quantity'] and product1['product_sale_uom'] == product['product_sale_uom']:
#                     if product['date_start'] and product['date_end']:
#                         if product1['date_start'] <= product['date_end']:
#                             count += 1
#                     elif product['date_start'] == False and product['date_end'] == False:
#                         count += 1
#                     elif product['date_start'] and product['date_end'] == False:
#                         count += 1
#                     else:
#                         if product['date_start'] <= product1['date_end']:
#                             count += 1
#
#         else:
#             for product in product_list:
#                 if product1['product_name'] == product['product_name'] and product1['min_quantity'] == product[
#                     'min_quantity'] and product1['product_sale_uom'] == product['product_sale_uom']:
#                     if product['date_start'] and product['date_end']:
#                         if product1['date_end'] >= product['date_start']:
#                             count += 1
#                     elif product['date_start'] == False and product['date_end'] == False:
#                         count += 1
#                     elif product['date_start'] and product['date_end'] == False:
#                         if product1['date_end'] >= product['date_start']:
#                             count += 1
#                     else:
#                         count += 1
#
#     if count != 1:
#         raise ValidationError('该价格表已经存在这个规格的产品，请勿重复创建')


# 发票明细行同步销售订单明细行小计
class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    product_sale_num = fields.Float(string='number', required=True, default=1)

    # 该表传入的参数，实现发票明细行的重新计算
    @api.one
    @api.depends('price_unit', 'discount', 'invoice_line_tax_ids', 'quantity',
                 'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id', 'invoice_id.company_id',
                 'invoice_id.date_invoice', 'invoice_id.date')
    def _compute_price(self):
        currency = self.invoice_id and self.invoice_id.currency_id or None
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        taxes = False
        if self.invoice_line_tax_ids:
            taxes = self.invoice_line_tax_ids.compute_all(price, currency, self.quantity, product=self.product_id,
                                                          partner=self.invoice_id.partner_id)
        self.price_subtotal = price_subtotal_signed = taxes['total_excluded'] if taxes else self.quantity * price
        self.price_total = taxes['total_included'] if taxes else self.price_subtotal
        if self.invoice_id.currency_id and self.invoice_id.currency_id != self.invoice_id.company_id.currency_id:
            currency = self.invoice_id.currency_id
            date = self.invoice_id._get_currency_rate_date()
            price_subtotal_signed = currency._convert(price_subtotal_signed, self.invoice_id.company_id.currency_id,
                                                      self.company_id or self.env.user.company_id,
                                                      date or fields.Date.today())
        sign = self.invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1
        self.price_subtotal_signed = price_subtotal_signed * sign


# 发票未税金额，税率，总计同步销售订单
class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True,
                                     readonly=True, compute='_compute_amount', track_visibility='always')

    amount_tax = fields.Monetary(string='Tax', store=True,
                                 readonly=True, compute='_compute_amount')

    amount_total = fields.Monetary(string='Total', store=True,
                                   readonly=True, compute='_compute_amount')

    residual = fields.Monetary(string='Amount Due',
                               compute='_compute_residual', store=True, help="Remaining amount due.")

    @api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount', 'tax_line_ids.amount_rounding',
                 'currency_id', 'company_id', 'date_invoice', 'type')
    def _compute_amount(self):
        round_curr = self.currency_id.round
        self.amount_untaxed = sum(line.price_subtotal for line in self.invoice_line_ids)
        # self.amount_tax = sum(line.price_tax for line in self.invoice_line_ids)
        self.amount_tax = sum(round_curr(line.amount_total) for line in self.tax_line_ids)
        self.amount_total = self.amount_untaxed + self.amount_tax
        amount_total_company_signed = self.amount_total
        amount_untaxed_signed = self.amount_untaxed
        if self.currency_id and self.company_id and self.currency_id != self.company_id.currency_id:
            currency_id = self.currency_id
            amount_total_company_signed = currency_id._convert(self.amount_total, self.company_id.currency_id,
                                                               self.company_id,
                                                               self.date_invoice or fields.Date.today())
            amount_untaxed_signed = currency_id._convert(self.amount_untaxed, self.company_id.currency_id,
                                                         self.company_id, self.date_invoice or fields.Date.today())
        sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
        self.amount_total_company_signed = amount_total_company_signed * sign
        self.amount_total_signed = self.amount_total * sign
        self.amount_untaxed_signed = amount_untaxed_signed * sign

    @api.one
    @api.depends(
        'state', 'currency_id', 'invoice_line_ids.price_subtotal',
        'move_id.line_ids.amount_residual',
        'move_id.line_ids.currency_id')
    def _compute_residual(self):
        residual = 0.0
        residual_company_signed = 0.0
        sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
        for line in self.sudo().move_id.line_ids:
            if line.account_id == self.account_id:
                residual_company_signed += line.amount_residual
                if line.currency_id == self.currency_id:
                    residual += line.amount_residual_currency if line.currency_id else line.amount_residual
                else:
                    from_currency = line.currency_id or line.company_id.currency_id
                    residual += from_currency._convert(line.amount_residual, self.currency_id, line.company_id,
                                                       line.date or fields.Date.today())
        self.residual_company_signed = abs(residual_company_signed) * sign
        self.residual_signed = abs(residual) * sign
        self.residual = abs(residual)
        digits_rounding_precision = self.currency_id.rounding
        if float_is_zero(self.residual, precision_rounding=digits_rounding_precision):
            self.reconciled = True
        else:
            self.reconciled = False

    @api.multi
    def get_taxes_values(self):
        tax_grouped = {}
        for line in self.invoice_line_ids:
            if not line.account_id:
                continue
            price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.invoice_line_tax_ids.compute_all(price_unit, self.currency_id, line.quantity, line.product_id,
                                                          self.partner_id)['taxes']
            for tax in taxes:
                val = self._prepare_tax_line_vals(line, tax)
                key = self.env['account.tax'].browse(tax['id']).get_grouping_key(val)

                if key not in tax_grouped:
                    tax_grouped[key] = val
                else:
                    tax_grouped[key]['amount'] += val['amount']
                    tax_grouped[key]['base'] += val['base']
        return tax_grouped
