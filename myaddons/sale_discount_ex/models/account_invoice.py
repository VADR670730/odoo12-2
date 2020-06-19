# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import odoo.addons.decimal_precision as dp



class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
    _description = "Invoice"

    is_gross = fields.Boolean(u'Gross', default=False)
    discount_td = fields.Float(u'TD%', digits=dp.get_precision('Discount'), related='partner_id.discount_td',
                               readonly=True)
    discount_pd = fields.Float(u'PD%', digits=dp.get_precision('Discount'), related='partner_id.discount_pd',
                               readonly=True)
    discount_io = fields.Float(u'IO%', digits=dp.get_precision('Discount'), related='partner_id.discount_io',
                               readonly=True)
    discount_ot = fields.Float(u'OT%', digits=dp.get_precision('Discount'), related='partner_id.discount_ot',
                               readonly=True)



class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'
    _description = "Invoice Line"

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




