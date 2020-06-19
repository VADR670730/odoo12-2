# -*- coding: utf-8 -*-

from odoo import models, fields, api
import random

'''
value = {'extract_state': 'no_extract_requested', 'type': 'in_invoice', 'purchase_id': False, 'move_name': False,
         'currency_id': 32, 'comment': False, 'user_id': 2, 'journal_id': 2, 'incoterm_id': False, 'company_id': 1,
         'sequence_number_next': False, 'partner_id': 40, 'reference': False, 'vendor_bill_id': False,
         'vendor_bill_purchase_id': False, 'origin': 'PO00064', 'source_email': False, 'date_invoice': False,
         'date_due': False, 'partner_bank_id': False,

         'invoice_line_ids': [[0, 'virtual_11423',
                               {'analytic_tag_ids': [[6, False, []]],
                                'invoice_line_tax_ids': [[6, False, [9]]],
                                'name': 'PO00064: [00072] Goat Soap 原味羊奶手工皂',
                                'sequence': 0, 'uom_id': 1,
                                'product_id': 232, 'account_id': 67,
                                'price_unit': 23, 'quantity': 2,
                                'discount': 0,
                                'account_analytic_id': False,
                                'currency_id': 32, 'purchase_line_id': 235,
                                'purchase_id': 64}]],

         'tax_line_ids': [[0, 'virtual_11436',
                           {'analytic_tag_ids': [[6, False, []]], 'name': '税收16％ - 中国小企业会计科目表', 'tax_id': 9,
                            'account_id': 43,
                            'account_analytic_id': False, 'amount': 7.36, 'amount_rounding': 0, 'manual': False,
                            'sequence': 1,
                            'currency_id': 32}]],

         'account_id': 40, 'date': False, 'name': False, 'fiscal_position_id': False,
         'payment_term_id': False, 'message_attachment_count': 0}
'''

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def _get_random_num(self, seq):
        num = "".join(str(i) for i in random.sample(range(0, 9), seq))
        return num

    def prepare_invoice(self):

        context_1 = {
                     'type': 'in_invoice',
                     'default_purchase_id': self.id,
                     'default_currency_id': self.currency_id.id,
                     'default_company_id': self.company_id.id,
                     'search_disable_custom_filters': True}

        journal_id = self.env["account.invoice"].with_context(context_1)._default_journal()
        journal_id = journal_id.id if journal_id else 2

        account_id = self.env["account.account"].search([["name","=","应付账款"],["company_id",'=',self.company_id.id],["user_type_id.name","=","应付"]])

        account_id = account_id.id if len(account_id) == 1 else 40

        account_id_ = self.env["account.account"].search([["name","=","主营业务成本"],["company_id",'=',self.company_id.id],["user_type_id.name","=","费用"]])

        account_id_ = account_id_.id if len(account_id_) == 1 else 67


        value = {'extract_state': 'no_extract_requested', 'type': 'in_invoice', 'purchase_id': False,
                         'move_name': False,
                         'currency_id': self.currency_id.id, 'comment': False, 'journal_id': journal_id, 'incoterm_id': False, 'company_id': self.company_id.id,
                         'sequence_number_next': False, 'reference': False, 'vendor_bill_id': False,
                         'vendor_bill_purchase_id': False, 'source_email': False, 'date_invoice': False,
                         'date_due': False, 'partner_bank_id': False,
                         'account_id': account_id, 'date': False, 'name': False, 'fiscal_position_id': False,
                         'payment_term_id': False, 'message_attachment_count': 0}

        value['user_id'] = self._context.get("uid", False)
        value['partner_id'] = self.partner_id.id or False
        value['origin'] = self.name or False
        temp_list = []
        tax_ids = []
        for line in self.mapped("order_line"):
            invoice_line_ids = [0, "virtual_" + self._get_random_num(5)]
            temp = {'analytic_tag_ids': [[6, False, []]],
                                                'invoice_line_tax_ids': [[6, False,line.taxes_id.ids]],
                                                'sequence': 0,
                                                'account_id': account_id_,
                                                'discount': 0,
                                                'account_analytic_id': False,
                                                }
            tax_ids += line.taxes_id.ids

            temp['name'] = line.name
            temp['uom_id'] = line.product_uom.id
            temp['product_id'] = line.product_id.id
            temp['price_unit'] = line.price_unit
            temp['quantity'] = line.product_qty
            temp['currency_id'] = self.currency_id.id
            temp['purchase_line_id'] = line.id
            temp['purchase_id'] = self.id
            invoice_line_ids.append(temp)
            temp_list.append(invoice_line_ids)

        value['invoice_line_ids'] = temp_list

        tax_ids = list(set(tax_ids))
        tax_line_list = []
        for tax_id in tax_ids:
            tax_obj = self.env['account.tax'].browse(tax_id)
            tax_line = [0, 'virtual_'+self._get_random_num(5),
                                               {'analytic_tag_ids': [[6, False, []]], 'name': tax_obj.name,
                                                'tax_id': tax_id, 'account_id': tax_obj.account_id.id,
                                                'account_analytic_id': False, 'amount': self.amount_tax, 'amount_rounding': 0,
                                                'manual': False, 'sequence': 1,
                                                'currency_id': self.currency_id.id}]
            tax_line_list.append(tax_line)

        value['tax_line_ids'] = tax_line_list

        return value

    @api.multi
    def create_invoice(self):

        for order in self:
           # state = {'invisible': ['|', ('state', 'not in', ('purchase')), ('invoice_status', 'in', ('no', 'invoiced'))]}
            if order.state == 'done' and order.invoice_count == 0:
                order.button_unlock()
            if order.state == "purchase" and order.invoice_count == 0:
                value = order.prepare_invoice()
                context = {
                 'create_bill': True, 'active_model': 'purchase.order',
                 'type': 'in_invoice',
                 'search_disable_custom_filters': True}
                invoice = self.env["account.invoice"].with_context(context).create(value)

        return True