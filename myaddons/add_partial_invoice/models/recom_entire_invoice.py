# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    @api.model
    def _get_advance_payment_method(self):
        if self._count() == 1:
            sale_obj = self.env['sale.order']
            order = sale_obj.browse(self._context.get('active_ids'))[0]
            flag_1 = order.order_line.filtered(lambda dp: dp.is_downpayment)
            flag_2 = order.invoice_ids.filtered(lambda invoice: invoice.state != 'cancel')
            flag_3 = order.order_line.filtered(lambda l: l.qty_to_invoice < 0)
            if flag_1 and flag_2 or flag_3:
                return 'all'
            else:
                return 'delivered'
        return 'all'

    advance_payment_method = fields.Selection([
        ('delivered', '可开票的明细行'),
        ('all', '可开具发票明细 ( 扣除预付定金 )'),
        ('percentage', '预收定金(百分比)'),
        ('fixed', '预收定金(固定总额)')
    ], string='What do you want to invoice?', default=_get_advance_payment_method, required=True)


# class SaleOrder(models.Model):
#     _inherit = "sale.order"
#
#     @api.multi
#     def create_partial_invoice(self):
#         '''
#         部分开票的向导跳转方法
#         :return:
#         '''
#
#         obj = self.env['sale.order.line'].search([('order_id', '=', self.id)])
#
#         vals = ({'order_ids': [(6, 0, obj.ids)]})
#
#         a = self.env['add.partial.inv'].create(vals)
#         print('a', a)
#
#         return {
#             'name': u'部分开票',
#             "type": "ir.actions.act_window",
#             "res_model": "add.partial.inv",
#             'view_mode': 'form',
#             "view_type": "form",
#             'views': [(False, 'form')],
#             'target': 'new',
#             'context': "{'order_id': %s}" % self.id
#         }
#
#
# class SaleOrderLine(models.Model):
#     _inherit = "sale.order.line"
#
#     partial_id = fields.Many2one('add.partial.inv', string=u'部分开票')
#     # product_id = fields.Many2one('sale.order.line', string=u'产品')
#     inv_number = fields.Integer(string=u'开票数量')
#     inv_price = fields.Float(string=u'开票单价')
#     # uom_id = fields.Many2one('uom.uom', string=u'计量单位')
#     inv_amount = fields.Float(string=u'开票金额')
#     inved_number = fields.Integer(string=u'已开票数量')
#     noinv_number = fields.Integer(string=u'未开票数量')
#     inv_identifier = fields.Char(string=u'发票号码')
