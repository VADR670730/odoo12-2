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


class sale_order(models.Model):
    _inherit = 'sale.order'
    _description = u'Sale.Order'

    is_gross = fields.Boolean(u'Gross', default=False)
    discount_td = fields.Float(u'TD%', digits=dp.get_precision('Discount'), related='partner_id.discount_td',
                               readonly=True)
    discount_pd = fields.Float(u'PD%', digits=dp.get_precision('Discount'), related='partner_id.discount_pd',
                               readonly=True)
    discount_io = fields.Float(u'IO%', digits=dp.get_precision('Discount'), related='partner_id.discount_io',
                               readonly=True)
    discount_ot = fields.Float(u'OT%', digits=dp.get_precision('Discount'), related='partner_id.discount_ot',
                               readonly=True)
    x_guest_supplier_code = fields.Char('Guest Code',related = 'partner_id.x_guest_supplier_code',readonly = True, help='客方内部对供应商（我司）的编码')
    x_customer_designated_positions = fields.Char('Warehouse No',help='客户指定的仓库内收货位置')

    @api.multi
    def _prepare_invoice(self):
        invoice_vals = super(sale_order, self)._prepare_invoice()
        invoice_vals['incoterms_id'] = self.incoterm.id or False
        invoice_vals['is_gross'] = self.is_gross or False
        return invoice_vals

class sale_order_line(models.Model):
    _inherit = 'sale.order.line'
    _description = u'Sale.Order.line'

    discount_td = fields.Float(u'TD%', digits=dp.get_precision('Discount'))
    discount_pd = fields.Float(u'PD%', digits=dp.get_precision('Discount'))
    discount_io = fields.Float(u'IO%', digits=dp.get_precision('Discount'))
    discount_ot = fields.Float(u'OT%', digits=dp.get_precision('Discount'))

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id',
                 'order_id.is_gross', 'discount_td', 'discount_pd', 'discount_io', 'discount_ot')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            # price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            if line.order_id.is_gross:
                price = line.price_unit * (1 - (line.discount_td or 0.0) / 100.0
                                           - (line.discount_pd or 0.0) / 100.0
                                           - (line.discount_io or 0.0) / 100.0
                                           - (line.discount_ot or 0.0) / 100.0)
            else:
                price = line.price_unit * (1 - (line.discount_td or 0.0) / 100.0) \
                        * (1 - (line.discount_pd or 0.0) / 100.0) \
                        * (1 - (line.discount_io or 0.0) / 100.0) \
                        * (1 - (line.discount_ot or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty,
                                            product=line.product_id, partner=line.order_id.partner_shipping_id)
            line.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })


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
            'quantity': qty,
            'discount': self.discount,
            'uom_id': self.product_uom.id,
            'product_id': self.product_id.id or False,
            'invoice_line_tax_ids': [(6, 0, self.tax_id.ids)],
            'account_analytic_id': self.order_id.analytic_account_id.id,
            'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
            'display_type': self.display_type,
            'discount_td': self.discount_td,
            'discount_pd': self.discount_pd,
            'discount_io': self.discount_io,
            'discount_ot': self.discount_ot
        }
        return res