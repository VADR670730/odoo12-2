# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    barcode = fields.Char(string='产品条码', related='product_id.barcode', readonly=True)


class PurchaseOrderLine(models.Model):

    _inherit = 'purchase.order.line'

    barcode = fields.Char(string='产品条码', related='product_id.barcode', readonly=True)


class StockMove(models.Model):
    _inherit = 'stock.move'

    barcode = fields.Char(string='产品条码', related='product_id.barcode', readonly=True)


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'
    barcode = fields.Char(string='产品条码', related='product_id.barcode', readonly=True)


