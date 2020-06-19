# -*- coding: utf-8 -*-
from odoo import http

# class StockLotExSwitch(http.Controller):
#     @http.route('/stock_lot_ex_switch/stock_lot_ex_switch/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/stock_lot_ex_switch/stock_lot_ex_switch/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('stock_lot_ex_switch.listing', {
#             'root': '/stock_lot_ex_switch/stock_lot_ex_switch',
#             'objects': http.request.env['stock_lot_ex_switch.stock_lot_ex_switch'].search([]),
#         })

#     @http.route('/stock_lot_ex_switch/stock_lot_ex_switch/objects/<model("stock_lot_ex_switch.stock_lot_ex_switch"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('stock_lot_ex_switch.object', {
#             'object': obj
#         })