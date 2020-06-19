# # -*- coding: utf-8 -*-
#
# from odoo import models, fields, api
#
#
# class SaleOrderLine(models.Model):
#
#     def get_default_sequence(self):
#         sub_nums = self._context.get('sub_nums')
#         sub_nums = sub_nums or 0
#         return sub_nums + 1
#
#     _inherit = 'sale.order.line'
#     show_sequence = fields.Integer(string="序号", readonly=True, default=get_default_sequence,
#                                    compute="_compute_show_sequence")
#
#     @api.multi
#     def _compute_show_sequence(self):
#         num = 1
#         order_lines = self.sorted(key=lambda line: (line.sequence, line.id))
#         for line in order_lines:
#             line.show_sequence = num
#             num += 1
#
#
# class SaleOrder(models.Model):
#     _inherit = "sale.order"
#
#     sub_nums = fields.Integer(string="销售订单明细行数量", compute='_compute_sub_nums')
#
#     @api.onchange('order_line')
#     def _compute_sub_nums(self):
#         nums = len(self.order_line)
#         self.sub_nums = nums
#
#     @api.onchange('order_line')
#     def _onchange_sequence_(self):
#         order_lines = self.order_line.sorted(key=lambda line: (line.sequence, line.show_sequence))
#         num = 1
#         for line in order_lines:
#             line.show_sequence = num
#             num += 1
#
#
# class PurchaseOrderLine(models.Model):
#
#     _inherit = 'purchase.order.line'
#
#     def get_default_sequence(self):
#         sub_nums = self._context.get('sub_nums')
#         sub_nums = sub_nums or 0
#         return sub_nums + 1
#
#     show_sequence = fields.Integer(string="序号", readonly=True, default=get_default_sequence,
#                                    compute="_compute_show_sequence")
#
#     @api.multi
#     def _compute_show_sequence(self):
#         num = 1
#         order_lines = self.sorted(key=lambda line: (line.sequence, line.id))
#         for line in order_lines:
#             line.show_sequence = num
#             num += 1
#
#
# class PurchaseOrder(models.Model):
#     _inherit = "purchase.order"
#
#     sub_nums = fields.Integer(string="采购订单明细行数量", compute='_compute_sub_nums')
#
#     @api.onchange('order_line')
#     def _compute_sub_nums(self):
#         nums = len(self.order_line)
#         self.sub_nums = nums
#
#     @api.onchange('order_line')
#     def _onchange_sequence_(self):
#         order_lines = self.order_line.sorted(key=lambda line: (line.sequence, line.show_sequence))
#         num = 1
#         for line in order_lines:
#             line.show_sequence = num
#             num += 1
#
#
# class StockMove(models.Model):
#     _inherit = 'stock.move'
#
#     def get_default_sequence(self):
#         sub_nums = self._context.get('sub_nums')
#         sub_nums = sub_nums or 0
#         return sub_nums + 1
#
#
#     show_sequence = fields.Integer(string="序号", readonly=True, default=get_default_sequence,
#                                    compute="_compute_show_sequence")
#
#
#     @api.multi
#     def read(self, fields=None, load='_classic_read'):
#         if len(self) == 1:
#             self.show_sequence = 1
#         res = super().read(fields=fields, load='_classic_read')
#         return res
#
#     @api.multi
#     def _compute_show_sequence(self):
#         num = 1
#         order_lines = self.sorted(key=lambda line: (line.sequence,line.id))
#         for line in order_lines:
#             line.show_sequence = num
#             num += 1
#
# class Picking(models.Model):
#     _inherit = "stock.picking"
#
#     sub_nums = fields.Integer(string="调拨订单明细行数量", compute='_compute_sub_nums')
#
#     @api.onchange('move_ids_without_package')
#     def _compute_sub_nums(self):
#         for picking in self:
#             nums = len(picking.move_ids_without_package)
#             picking.sub_nums = nums
#
#     @api.onchange('move_ids_without_package')
#     def _onchange_sequence_(self):
#         order_lines = self.move_ids_without_package.sorted(key=lambda line: (line.sequence, line.show_sequence))
#         num = 1
#         for line in order_lines:
#             line.show_sequence = num
#             num += 1
