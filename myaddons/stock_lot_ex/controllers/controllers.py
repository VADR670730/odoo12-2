# -*- coding: utf-8 -*-
from odoo import http

# class StockLotEx(http.Controller):
#     @http.route('/stock_lot_ex/stock_lot_ex/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/stock_lot_ex/stock_lot_ex/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('stock_lot_ex.listing', {
#             'root': '/stock_lot_ex/stock_lot_ex',
#             'objects': http.request.env['stock_lot_ex.stock_lot_ex'].search([]),
#         })

#     @http.route('/stock_lot_ex/stock_lot_ex/objects/<model("stock_lot_ex.stock_lot_ex"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('stock_lot_ex.object', {
#             'object': obj
#         })