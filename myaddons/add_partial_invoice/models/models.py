# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AddPartialInv(models.Model):
    _name = "add.partial.inv"

    @api.model
    def _create_inv(self):
        order = self.get_context()
        print('order', order)
        obj = self.env['sale.order.line'].search([('order_id', '=', order.id)])
        print('obj', obj.ids)
        self.order_ids = ([6, 0, obj.ids])

    order_ids = fields.One2many('sale.order.line', 'partial_id', string=u'订单行')
    # product_id = fields.Many2one('sale.order.line', string=u'产品')
    # inv_number = fields.Integer(string=u'开票数量')
    # inv_price = fields.Float(string=u'开票单价')
    # uom_id = fields.Many2one('uom.uom', string=u'计量单位')
    # inv_amount = fields.Float(string=u'开票金额')
    # inved_number = fields.Integer(string=u'已开票数量')
    # noinv_number = fields.Integer(string=u'未开票数量')
    # inv_identifier = fields.Char(string=u'发票号码')

    @api.multi
    def get_context(self):
        print(self._context.get('order_id'), 333)
        trade_leads = self.env['sale.order'].browse(self._context.get('order_id'))
        return trade_leads

