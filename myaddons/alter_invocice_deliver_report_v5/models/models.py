# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import odoo.addons.decimal_precision as dp



class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    is_gross = fields.Boolean(u'Gross', default=False)




class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    discount_td = fields.Float(u'TD%', digits=dp.get_precision('Discount'))
    discount_pd = fields.Float(u'PD%', digits=dp.get_precision('Discount'))
    discount_io = fields.Float(u'IO%', digits=dp.get_precision('Discount'))
    discount_ot = fields.Float(u'OT%', digits=dp.get_precision('Discount'))

    @api.one
    @api.depends('price_unit', 'discount', 'invoice_line_tax_ids', 'quantity',
        'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id', 'invoice_id.company_id',
        'invoice_id.date_invoice', 'invoice_id.date','discount_td', 'discount_pd', 'discount_io', 'discount_ot','invoice_id.is_gross')
    def _compute_price(self):
        currency = self.invoice_id and self.invoice_id.currency_id or None
        # price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        for line in self:
            if line.invoice_id.is_gross:
                price = line.price_unit * (1 - (line.discount_td or 0.0) / 100.0
                                           - (line.discount_pd or 0.0) / 100.0
                                           - (line.discount_io or 0.0) / 100.0
                                           - (line.discount_ot or 0.0) / 100.0)
            else:
                price = line.price_unit * (1 - (line.discount_td or 0.0) / 100.0) \
                        * (1 - (line.discount_pd or 0.0) / 100.0) \
                        * (1 - (line.discount_io or 0.0) / 100.0) \
                        * (1 - (line.discount_ot or 0.0) / 100.0)
        taxes = False
        if self.invoice_line_tax_ids:
            taxes = self.invoice_line_tax_ids.compute_all(price, currency, self.quantity, product=self.product_id, partner=self.invoice_id.partner_id)
        self.price_subtotal = price_subtotal_signed = taxes['total_excluded'] if taxes else self.quantity * price
        # self.price_subtotal = price_subtotal_signed = 50
        self.price_total = taxes['total_included'] if taxes else self.price_subtotal
        if self.invoice_id.currency_id and self.invoice_id.currency_id != self.invoice_id.company_id.currency_id:
            currency = self.invoice_id.currency_id
            date = self.invoice_id._get_currency_rate_date()
            price_subtotal_signed = currency._convert(price_subtotal_signed, self.invoice_id.company_id.currency_id, self.company_id or self.env.user.company_id, date or fields.Date.today())
        sign = self.invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1
        self.price_subtotal_signed = price_subtotal_signed * sign

        price_total = self.price_total
        price_subtotal = self.price_subtotal
        price_subtotal_signed = self.price_subtotal_signed
        print('ok')




class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

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


# class SaleOrder(models.Model):
#     _inherit = "sale.order"
#
#     x_guest_supplier_code = fields.Char(string="Guest code",help='客方内部对供应商（我司）的编码客方编码',readonly = True)
#     x_customer_designated_positions = fields.Char(string="Warehouse No",help="客户指定的仓库内收货位置")
#
#
#     @api.multi
#     def _prepare_invoice(self):
#         invoice_vals = super(SaleOrder, self)._prepare_invoice()
#         invoice_vals['incoterms_id'] = self.incoterm.id or False
#         invoice_vals['is_gross'] = self.is_gross or False
#         return invoice_vals

