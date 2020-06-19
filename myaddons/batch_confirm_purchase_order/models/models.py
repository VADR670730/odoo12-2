# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.multi
    def action_confirm_(self):
        res = True
        # for order in self:
        #     if order.state not in ['done', 'cancel']:
        #         res = order.action_confirm()
        res = self.button_confirm()
        return res