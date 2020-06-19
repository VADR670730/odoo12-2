# -*- encoding: utf-8 -*-
from odoo import models, fields, api


class ChangeInvoiceAmountWizard(models.TransientModel):
    _name = 'change.invoice.amount.wizard'
    _description = u'更改批量付款发票金额'

    @api.one
    def get_invoice_record(self):
        self.ensure_one()
        print("get_invoice_record")
        obj = self._context.get('trade_leads')
        print(1, obj)
        self.invoice_ids = [(6, 0, self)]
        print(2, self.invoice_ids)

    invoice_ids = fields.Many2many('account.invoice', string='所选发票', default=get_invoice_record)

    def action_update_amount(self):
        return {
            'name': u'登记付款',
            "type": "ir.actions.act_window",
            "res_model": "account.register.payments",
            'view_mode': 'form',
            "view_type": "form",
            'views': [(False, 'form')],
            'target': 'new',
            'context': "{'invoice_ids': %s}" % self.invoice_ids.ids
        }

    @api.multi
    def get_context(self):
        print(self._context.get('trade_leads'), 333)
        trade_leads = self.env['account.invoice'].browse(self._context.get('trade_leads'))
        return trade_leads
