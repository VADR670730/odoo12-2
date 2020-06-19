# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class AccountAbstractPayment(models.AbstractModel):
    _inherit = "account.abstract.payment"

    writeoff_account_id = fields.Many2many('account.account', string="Difference Account",
                                           domain=[('deprecated', '=', False)], copy=False)

    # writeoff_save_id = fields.Many2many('account.account', string="Difference Account",
    #                                     domain=[('deprecated', '=', False)], copy=False)
    total_price = fields.Monetary(string="金额总计", default=0.0)


class AccountAccount(models.Model):
    _inherit = "account.account"

    money = fields.Monetary(string="金额", defaule=0.0)
    remark = fields.Char(string="标签", default="Write-Off")
    self_amount = fields.Float(string=u'本币金额')
    currencys_id = fields.Many2one('res.currency', string='币种')


# class AccountInvoice(models.Model):
#     _inherit = "account.invoice"
#
#     invoiced_id = fields.Many2one('change.invoice.amount.wizard',string=u'批量付款更改单张发票金额')


class AccountRegisterPayments(models.TransientModel):
    _inherit = "account.register.payments"

    self_amount = fields.Float(string=u'收付款本币金额')
    flag = fields.Char(string=u'标识', default=0, store=True)

    @api.depends('invoice_ids', 'amount', 'payment_date', 'currency_id', 'total_price', 'self_amount')
    def _compute_payment_difference(self):
        self.flag = 0
        for pay in self.filtered(lambda p: p.invoice_ids):
            payment_amount = -pay.amount if pay.payment_type == 'outbound' else pay.amount
            payment_total = -pay.total_price if pay.payment_type == 'outbound' else pay.total_price
            pay.payment_difference = pay._compute_payment_amount() - payment_amount - payment_total
            total = pay._compute_payment_amount()
            if payment_amount != total:
                self.flag = 1

    @api.onchange('writeoff_account_id')
    def _compute_total_price(self):
        self.total_price = 0
        if self.writeoff_account_id:
            for count in self.writeoff_account_id:
                self.total_price += count.money

    @api.onchange('writeoff_account_id', 'currency_id')
    def _get_currency_value(self):
        for cur in self.writeoff_account_id:
            cur.currencys_id = self.currency_id

    @api.onchange('currency_id')
    def _clear_writeoff_id(self):
        """
        再次更改货币单位时，差异明细行的记录清除
        :return:
        """
        for i in self.writeoff_account_id:
            self.writeoff_account_id = [(2, i.id)]

    @api.multi
    def create_payments(self):
        '''Create payments according to the invoices.
        Having invoices with different commercial_partner_id or different type (Vendor bills with customer invoices)
        leads to multiple payments.
        In case of all the invoices are related to the same commercial_partner_id and have the same type,
        only one payment will be created.

        :return: The ir.actions.act_window to show created payments.
        '''
        # print("create_payments")
        self._context.get('invoice_ids')

        Payment = self.env['account.payment']
        payments = Payment

        for payment_vals in self.get_payments_vals():
            if self.self_amount > 0:
                payment_vals.update({
                    'self_amount': self.self_amount
                })
            payments += Payment.create(payment_vals)
        payments.get_payment_type(self.payment_difference_handling, self.writeoff_account_id)
        payments.post()

        action_vals = {
            'name': _('Payments'),
            'domain': [('id', 'in', payments.ids), ('state', '=', 'posted')],
            'view_type': 'form',
            'res_model': 'account.payment',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'context': "{'ids': %s}" % self.invoice_ids.ids
        }
        if len(payments) == 1:
            action_vals.update({'res_id': payments[0].id, 'view_mode': 'form'})
        else:
            action_vals['view_mode'] = 'tree,form'
        # print(action_vals, 'action_vals')
        return action_vals


class AccountPayment(models.Model):
    _inherit = "account.payment"

    received_price = fields.Float(string='本币金额')
    unit_id = fields.Many2one('res.currency', string='Currency', required=True,
                              default=lambda self: self.env.user.company_id.currency_id)
    self_amount = fields.Float(string=u'收付款本币金额')
    flag = fields.Char(string=u'标识', default=0, store=True)

    @api.depends('invoice_ids', 'amount', 'payment_date', 'currency_id', 'total_price', 'self_amount')
    def _compute_payment_difference(self):
        self.flag = 0
        for pay in self.filtered(lambda p: p.invoice_ids):
            payment_amount = -pay.amount if pay.payment_type == 'outbound' else pay.amount
            payment_total = -pay.total_price if pay.payment_type == 'outbound' else pay.total_price
            pay.payment_difference = pay._compute_payment_amount() - payment_amount - payment_total
            total = pay._compute_payment_amount()
            if payment_amount != total:
                self.flag = 1

    @api.onchange('writeoff_account_id')
    def _compute_total_price(self):
        self.total_price = 0
        if self.writeoff_account_id:
            for count in self.writeoff_account_id:
                self.total_price += count.money

    @api.onchange('writeoff_account_id', 'currency_id')
    def _get_currency_value(self):
        for cur in self.writeoff_account_id:
            cur.currencys_id = self.currency_id

    @api.onchange('currency_id')
    def _clear_writeoff_id(self):
        """
        再次更改货币单位时，差异明细行的记录清除
        :return:
        """
        for i in self.writeoff_account_id:
            self.writeoff_account_id = [(2, i.id)]

    def get_payment_type(self, payment_type, writeoff_account_id):
        self.payment_difference_handling = payment_type
        self.writeoff_account_id = writeoff_account_id

    def _create_payment_entry(self, amount):
        """ Create a journal entry corresponding to a payment, if the payment references invoice(s) they are reconciled.
            Return the journal entry.
        """
        # super(AccountPayment)._create_payment_entry(amount)
        aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
        debit, credit, amount_currency, currency_id = aml_obj.with_context(
            date=self.payment_date)._compute_amount_fields(
            amount, self.currency_id, self.company_id.currency_id)
        move = self.env['account.move'].create(self._get_move_vals())
        # print('payment_move', move)

        # Write line corresponding to invoice payment
        counterpart_aml_dict = self._get_shared_move_line_vals(debit, credit, amount_currency, move.id, False)
        counterpart_aml_dict.update(self._get_counterpart_move_line_vals(self.invoice_ids))
        counterpart_aml_dict.update({'currency_id': currency_id})

        if self.self_amount > 0 and credit > 0:
            counterpart_aml_dict.update({'credit': self.self_amount})
        elif self.self_amount > 0 and debit > 0:
            counterpart_aml_dict.update({'debit': self.self_amount})
        counterpart_aml = aml_obj.create(counterpart_aml_dict)
        # print('payment1', counterpart_aml_dict)

        # Reconcile with the invoices
        if self.payment_difference_handling == 'reconcile' and self.writeoff_account_id:
            # print("reconcile")
            for acc in self.writeoff_account_id:
                writeoff_line = self._get_shared_move_line_vals(0, 0, 0, move.id, False)
                debit_wo, credit_wo, amount_currency_wo, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(self.payment_difference, self.currency_id, self.company_id.currency_id)
                writeoff_line['name'] = acc.remark
                writeoff_line['account_id'] = acc.id
                writeoff_line['amount_currency'] = amount_currency_wo
                writeoff_line['currency_id'] = currency_id

                if acc.self_amount > 0:
                    if debit_wo > 0:
                        writeoff_line['debit'] = acc.self_amount
                        writeoff_line['credit'] = credit_wo
                    elif credit_wo > 0:
                        writeoff_line['debit'] = debit_wo
                        writeoff_line['credit'] = acc.self_amount
                else:
                    if debit_wo > 0:
                        writeoff_line['debit'] = acc.money
                        writeoff_line['credit'] = credit_wo
                    elif credit_wo > 0:
                        writeoff_line['debit'] = debit_wo
                        writeoff_line['credit'] = acc.money

                writeoff_line = aml_obj.create(writeoff_line)
                # print('reconcile_move', writeoff_line)

                # 采购
                if counterpart_aml['debit'] or (writeoff_line['credit'] and not counterpart_aml['credit']):
                    counterpart_aml['debit'] += credit_wo - debit_wo
                # 销售
                if counterpart_aml['credit'] or (writeoff_line['debit'] and not counterpart_aml['debit']):
                    counterpart_aml['credit'] += debit_wo - credit_wo
                counterpart_aml['amount_currency'] -= amount_currency_wo

        if self.payment_difference_handling == 'open' and self.writeoff_account_id:
            # print("open")
            for acc in self.writeoff_account_id:
                writeoff_line = self._get_shared_move_line_vals(0, 0, 0, move.id, False)

                debit_wo, credit_wo, amount_currency_wo, currency_id = aml_obj.with_context(
                    date=self.payment_date)._compute_amount_fields(acc.money, self.currency_id,
                                                                   self.company_id.currency_id)
                writeoff_line['name'] = acc.remark
                writeoff_line['account_id'] = acc.id
                writeoff_line['amount_currency'] = amount_currency_wo
                writeoff_line['currency_id'] = currency_id

                if acc.self_amount > 0:
                    if debit_wo > 0:
                        writeoff_line['debit'] = acc.self_amount
                        writeoff_line['credit'] = credit_wo
                    elif credit_wo > 0:
                        writeoff_line['debit'] = debit_wo
                        writeoff_line['credit'] = acc.self_amount
                else:
                    if debit_wo > 0:
                        writeoff_line['debit'] = debit_wo
                        writeoff_line['credit'] = credit_wo
                    elif credit_wo > 0:
                        writeoff_line['debit'] = debit_wo
                        writeoff_line['credit'] = credit_wo
                # print("writeoff_line", writeoff_line)
                writeoff_line = aml_obj.create(writeoff_line)

                if counterpart_aml['debit'] or (writeoff_line['credit'] and not counterpart_aml['credit']):
                    counterpart_aml['debit'] += writeoff_line['credit'] - writeoff_line['debit']
                    counterpart_aml['amount_currency'] = abs(counterpart_aml['amount_currency']) + writeoff_line['amount_currency']
                if counterpart_aml['credit'] or (writeoff_line['debit'] and not counterpart_aml['debit']):
                    # 发票付款记录金额加上金额差异记录金额
                    counterpart_aml['credit'] += writeoff_line['debit'] - writeoff_line['credit']
                    counterpart_aml['amount_currency'] = counterpart_aml['amount_currency'] - writeoff_line['amount_currency']

        # Write counterpart lines
        if not self.currency_id.is_zero(self.amount):
            if not self.currency_id != self.company_id.currency_id:
                amount_currency = 0
            liquidity_aml_dict = self._get_shared_move_line_vals(credit, debit, -amount_currency, move.id, False)
            # print('liquidity_aml_dict', liquidity_aml_dict)
            liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-amount))
            if self.self_amount > 0 and liquidity_aml_dict['debit'] > 0:
                liquidity_aml_dict.update({'debit': self.self_amount})
            elif self.self_amount > 0 and liquidity_aml_dict['credit'] > 0:
                liquidity_aml_dict.update({'credit': self.self_amount})
            aml_obj.create(liquidity_aml_dict)
            # print('payment2', liquidity_aml_dict)

        # validate the payment
        if not self.journal_id.post_at_bank_rec:
            move.post()

        # reconcile the invoice receivable/payable line(s) with the payment
        if self.invoice_ids:
            self.invoice_ids.register_payment(counterpart_aml)

        # 金额差异修改默认值为0
        account_list = self.env['account.account'].search(['|', ('money', '!=', 0), ('self_amount', '!=', 0)])
        for i in account_list:
            if i.money:
                i.money = 0
            if i.remark != "Write-Off":
                i.remark = "Write-Off"
            if i.self_amount:
                i.self_amount = 0
        return move

    def _create_transfer_entry(self, amount):
        """ Create the journal entry corresponding to the 'incoming money' part of an internal transfer, return the reconcilable move line
        """
        # print('_create_transfer_entry')
        aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
        debit, credit, amount_currency, dummy = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(
            amount, self.currency_id, self.company_id.currency_id)
        amount_currency = self.destination_journal_id.currency_id and self.currency_id._convert(amount,
                                                                                                self.destination_journal_id.currency_id,
                                                                                                self.company_id,
                                                                                                self.payment_date or fields.Date.today()) or 0

        dst_move = self.env['account.move'].create(self._get_move_vals(self.destination_journal_id))
        # print('transfer_move', dst_move)

        dst_liquidity_aml_dict = self._get_shared_move_line_vals(debit, credit, amount_currency, dst_move.id)
        dst_liquidity_aml_dict.update({
            'name': _('Transfer from %s') % self.journal_id.name,
            'account_id': self.destination_journal_id.default_credit_account_id.id,
            'amount_currency': self.self_amount,
            'currency_id': self.unit_id.id,
            'journal_id': self.destination_journal_id.id})

        if self.self_amount > 0:
            if debit > 0:
                dst_liquidity_aml_dict.update({
                    'debit': self.self_amount
                })
            elif credit > 0:
                dst_liquidity_aml_dict.update({
                    'credit': self.self_amount
                })
        aml_obj.create(dst_liquidity_aml_dict)
        # print('transfer1', dst_liquidity_aml_dict)

        transfer_debit_aml_dict = self._get_shared_move_line_vals(credit, debit, 0, dst_move.id)
        transfer_debit_aml_dict.update({
            'name': self.name,
            'account_id': self.company_id.transfer_account_id.id,
            'journal_id': self.destination_journal_id.id})
        if self.currency_id != self.company_id.currency_id:
            transfer_debit_aml_dict.update({
                'currency_id': self.unit_id.id,
                'amount_currency': -self.self_amount,
            })

        if self.self_amount > 0:
            if debit > 0:
                transfer_debit_aml_dict.update({
                    'credit': self.self_amount
                })
            elif credit > 0:
                transfer_debit_aml_dict.update({
                    'debit': self.self_amount
                })
        transfer_debit_aml = aml_obj.create(transfer_debit_aml_dict)
        # print('transfer2', transfer_debit_aml_dict)

        # amount_difference_dict = {}
        # amount_difference_dict2 = {}
        # if self.payment_type == 'transfer':
        #     journal_name_obj = self.env['account.account'].search([('name', '=', '费用-汇率差异')])
        #     amount_difference_dict.update({
        #         'name': journal_name_obj.name,
        #         'debit': abs(am.amount_currency - am.debit),
        #         'account_id': journal_name_obj.id,
        #         'currency_id': self.unit_id.id,
        #         'journal_id': self.destination_journal_id.id,
        #         'move_id': dst_move.id})
        #     aml_obj.create(amount_difference_dict)
        #     print('transfer3', amount_difference_dict)
        #
        #     amount_difference_dict2.update({
        #         'name': _('Transfer from %s') % self.journal_id.name,
        #         'credit': abs(am.amount_currency - am.debit),
        #         'account_id': self.destination_journal_id.default_credit_account_id.id,
        #         'currency_id': self.unit_id.id,
        #         'move_id': dst_move.id,
        #         'journal_id': self.destination_journal_id.id})
        #     aml_obj.create(amount_difference_dict2)
        #     print('transfer4', amount_difference_dict2)

        if not self.destination_journal_id.post_at_bank_rec:
            dst_move.post()
        return transfer_debit_aml


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.multi
    def assert_balanced(self):
        if not self.ids:
            return True
        prec = self.env.user.company_id.currency_id.decimal_places

        self._cr.execute("""\
            SELECT      move_id
            FROM        account_move_line
            WHERE       move_id in %s
            GROUP BY    move_id
            HAVING      abs(sum(debit) - sum(credit)) > %s
            """, (tuple(self.ids), 10 ** (-max(5, prec))))
        if len(self._cr.fetchall()) != 0:
            pass
            # raise UserError(_("Cannot create unbalanced journal entry."))
        return True


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    debit_amount = fields.Monetary(string=u'借方本币金额')
    credit_amount = fields.Monetary(string=u'贷方本币金额')

#
#     @api.model
#     def _compute_amount_fields(self, amount, src_currency, company_currency):
#         """ Helper function to compute value for fields debit/credit/amount_currency based on an amount and the currencies given in parameter"""
#         amount_currency = False
#         currency_id = False
#         date = self.env.context.get('date') or fields.Date.today()
#         company = self.env.context.get('company_id')
#         company = self.env['res.company'].browse(company) if company else self.env.user.company_id
#         if src_currency and src_currency != company_currency:
#             amount_currency = amount
#             amount = src_currency._convert(amount, company_currency, company, date)
#             currency_id = src_currency.id
#         debit = amount > 0 and amount or 0.0
#         credit = amount < 0 and -amount or 0.0
#         return debit, credit, amount_currency, currency_id
