# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockPickingReport(models.Model):
    _inherit = 'stock.move'

    @api.one
    def compute_stock_lot(self):
        lots_obj = []
        if self.product_id:
            lot_obj = self.env['stock.production.lot'].search([('product_id', '=', self.product_id.id)])
            for i in lot_obj:
                lots_obj.append(i.name)
        return lots_obj








