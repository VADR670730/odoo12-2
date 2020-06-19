# -*- coding: utf-8 -*-
from odoo import http

# class AddPartialInvoice(http.Controller):
#     @http.route('/add_partial_invoice/add_partial_invoice/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/add_partial_invoice/add_partial_invoice/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('add_partial_invoice.listing', {
#             'root': '/add_partial_invoice/add_partial_invoice',
#             'objects': http.request.env['add_partial_invoice.add_partial_invoice'].search([]),
#         })

#     @http.route('/add_partial_invoice/add_partial_invoice/objects/<model("add_partial_invoice.add_partial_invoice"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('add_partial_invoice.object', {
#             'object': obj
#         })