# -*- coding: utf-8 -*-
from odoo import http

# class AddSaleBarcode(http.Controller):
#     @http.route('/add_sale_barcode/add_sale_barcode/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/add_sale_barcode/add_sale_barcode/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('add_sale_barcode.listing', {
#             'root': '/add_sale_barcode/add_sale_barcode',
#             'objects': http.request.env['add_sale_barcode.add_sale_barcode'].search([]),
#         })

#     @http.route('/add_sale_barcode/add_sale_barcode/objects/<model("add_sale_barcode.add_sale_barcode"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('add_sale_barcode.object', {
#             'object': obj
#         })