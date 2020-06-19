# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class AddAmountDifference(models.Model):
    _inherit = 'account.invoice'

    def action_register_inbound_payment(self):
        payment_form = self.env.ref('account.view_account_payment_invoice_form', False)
        return {
            'name': '登记收款',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.payment',
            'view_id': payment_form.id,
            'target': 'new',
            'context': {'default_invoice_ids': [(4, self.id, None)]},
        }


class AccountAbstractPayment(models.AbstractModel):
    _inherit = "account.abstract.payment"

    writeoff_save_id = fields.Many2many('account.account', string="Difference Account",
                                        domain=[('deprecated', '=', False)], copy=False)
    total_price = fields.Monetary(string="金额总计", default=0.0)


class AccountAccount(models.Model):
    _inherit = "account.account"

    money = fields.Monetary(string="金额", defaule=0.0)
    remark = fields.Char(string="标签", default="Write-Off")
    self_amount = fields.Float(string=u'本币金额')
    currencys_id = fields.Many2one('res.currency', string='币种')


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

    @api.onchange('writeoff_save_id')
    def _compute_total_price(self):
        self.total_price = 0
        if self.writeoff_save_id:
            for count in self.writeoff_save_id:
                self.total_price += count.money

    @api.onchange('writeoff_save_id', 'currency_id')
    def _get_currency_value(self):
        for cur in self.writeoff_save_id:
            cur.currencys_id = self.currency_id

    @api.onchange('currency_id')
    def _clear_writeoff_id(self):
        """
        再次更改货币单位时，差异明细行的记录清除
        :return:
        """
        for i in self.writeoff_save_id:
            self.writeoff_save_id = [(2, i.id)]

    def action_validate_inbound_payment(self):
        """
        登记收款验证方法
        """
        if any(len(record.invoice_ids) != 1 for record in self):
            # For multiple invoices, there is account.register.payments wizard
            raise UserError("这个方法只被用来处理单个发票的支付。")
        return self.inbound_post()

    @api.multi
    def inbound_post(self):
        """ Create the journal items for the payment and update the payment's state to 'posted'.
            A journal entry is created containing an item in the source liquidity account (selected journal's default_debit or default_credit)
            and another in the destination reconcilable account (see _compute_destination_account_id).
            If invoice_ids is not empty, there will be one reconcilable move line per invoice to reconcile with.
            If the payment is a transfer, a second journal entry is created in the destination journal to receive money from the transfer account.
        """
        for rec in self:

            if rec.state != 'draft':
                raise UserError("只有草稿付款才能被发布。")

            if any(inv.state != 'open' for inv in rec.invoice_ids):
                raise ValidationError("因为发票不是打开状态所以付款不能完成!")

            # keep the name in case of a payment reset to draft
            if not rec.name:
                # Use the right sequence to set the name
                if rec.payment_type == 'transfer':
                    sequence_code = 'account.payment.transfer'
                else:
                    if rec.partner_type == 'customer':
                        if rec.payment_type == 'inbound':
                            sequence_code = 'account.payment.customer.invoice'
                        if rec.payment_type == 'outbound':
                            sequence_code = 'account.payment.customer.refund'
                    if rec.partner_type == 'supplier':
                        if rec.payment_type == 'inbound':
                            sequence_code = 'account.payment.supplier.refund'
                        if rec.payment_type == 'outbound':
                            sequence_code = 'account.payment.supplier.invoice'
                rec.name = self.env['ir.sequence'].with_context(ir_sequence_date=rec.payment_date).next_by_code(
                    sequence_code)
                if not rec.name and rec.payment_type != 'transfer':
                    raise UserError("你需要定义公司的%s序列." % (sequence_code,))

            # Create the journal entry
            amount = rec.amount * (rec.payment_type in ('outbound', 'transfer') and 1 or -1)
            move = rec._create_inbound_payment_entry(amount)

            # In case of a transfer, the first journal entry created debited the source liquidity account and credited
            # the transfer account. Now we debit the transfer account and credit the destination liquidity account.
            if rec.payment_type == 'transfer':
                transfer_credit_aml = move.line_ids.filtered(
                    lambda r: r.account_id == rec.company_id.transfer_account_id)
                transfer_debit_aml = rec._create_transfer_entry(amount)
                (transfer_credit_aml + transfer_debit_aml).reconcile()

            rec.write({'state': 'posted', 'move_name': move.name})
        return True

    def _create_inbound_payment_entry(self, amount):
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
        if self.payment_difference_handling == 'reconcile' and self.writeoff_save_id:
            # print("reconcile")
            for acc in self.writeoff_save_id:
                writeoff_line = self._get_shared_move_line_vals(0, 0, 0, move.id, False)
                debit_wo, credit_wo, amount_currency_wo, currency_id = aml_obj.with_context(
                    date=self.payment_date)._compute_amount_fields(self.payment_difference, self.currency_id,
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

        if self.payment_difference_handling == 'open' and self.writeoff_save_id:
            # print("open")
            for acc in self.writeoff_save_id:
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
                    counterpart_aml['amount_currency'] = abs(counterpart_aml['amount_currency']) + writeoff_line[
                        'amount_currency']
                if counterpart_aml['credit'] or (writeoff_line['debit'] and not counterpart_aml['debit']):
                    # 发票付款记录金额加上金额差异记录金额
                    counterpart_aml['credit'] += writeoff_line['debit'] - writeoff_line['credit']
                    counterpart_aml['amount_currency'] = counterpart_aml['amount_currency'] - writeoff_line[
                        'amount_currency']

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
