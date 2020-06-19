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
    _inherit='sale.order'
    

class sale_order_line(models.Model):
    _inherit = 'sale.order.line'

    @api.one
    @api.depends('sequence')
    def _compute_partner_product_ids(self):
        if self.order_id and self.order_id.partner_id:
            self.partner_product_ids= self.order_id.partner_id.partner_product_ids


    partner_product_id = fields.Many2one('res.partner.product', u'客户货品编码')
    partner_product_ids = fields.Many2many('res.partner.product', u'可选客户货品编码'
                                           , compute='_compute_partner_product_ids')

    @api.onchange('product_id')
    def product_id_change(self):
        if self.product_id:
            """由产品编号--->客户产品编号"""
            product = self.partner_product_ids.filtered(lambda x: x.product_id.id == self.product_id.id)
            if product:
                if product[-1] != self.partner_product_id:
                    self.partner_product_id = product[-1].id
            else:
                self.partner_product_id = False
        res = super(sale_order_line, self).product_id_change()
        if self.partner_product_id:
            self.update(dict(name='[%s] %s' % (self.partner_product_id.code, self.partner_product_id.name)))
        return res

    @api.onchange('partner_product_id')
    def onchange_partner_product_id(self):
        """由客户产品编号--->我们的产品编码"""
        if self.partner_product_id and self.partner_product_id.product_id:
            self.product_id = self.partner_product_id.product_id.id



    @api.multi
    def _create_backorder(self, backorder_moves=[]):
        """ Move all non-done lines into a new backorder picking. If the key 'do_only_split' is given in the context, then move all lines not in context.get('split', []) instead of all non-done lines.
        """
        # TDE note: o2o conversion, todo multi
        backorders = self.env['stock.picking']
        for picking in self:
            backorder_moves = backorder_moves or picking.move_lines
            if self._context.get('do_only_split'):
                not_done_bo_moves = backorder_moves.filtered(lambda move: move.id not in self._context.get('split', []))
            else:
                not_done_bo_moves = backorder_moves.filtered(lambda move: move.state not in ('done', 'cancel'))
            if not not_done_bo_moves:
                continue
            backorder_picking = picking.copy({
                'name': '/',
                'move_lines': [],
                'pack_operation_ids': [],
                'backorder_id': picking.id

            })
            picking.message_post(body=_("Back order <em>%s</em> <b>created</b>.") % (backorder_picking.name

                ))
            not_done_bo_moves.write({'picking_id': backorder_picking.id

            })
            if not picking.date_done:
                picking.write({'date_done': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)})
            backorder_picking.action_confirm()
            backorder_picking.action_assign()
            backorders |= backorder_picking
        return backorders
