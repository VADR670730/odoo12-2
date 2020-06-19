# -*- coding: utf-8 -*-
from odoo import http

# class BatchCreatePurchaseInvoice(http.Controller):
#     @http.route('/batch_create_purchase_invoice/batch_create_purchase_invoice/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/batch_create_purchase_invoice/batch_create_purchase_invoice/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('batch_create_purchase_invoice.listing', {
#             'root': '/batch_create_purchase_invoice/batch_create_purchase_invoice',
#             'objects': http.request.env['batch_create_purchase_invoice.batch_create_purchase_invoice'].search([]),
#         })

#     @http.route('/batch_create_purchase_invoice/batch_create_purchase_invoice/objects/<model("batch_create_purchase_invoice.batch_create_purchase_invoice"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('batch_create_purchase_invoice.object', {
#             'object': obj
#         })