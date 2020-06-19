# -*- coding: utf-8 -*-
from odoo import http

# class BatchConfirmSaleOrder(http.Controller):
#     @http.route('/batch_confirm_purchase_order/batch_confirm_purchase_order/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/batch_confirm_purchase_order/batch_confirm_purchase_order/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('batch_confirm_purchase_order.listing', {
#             'root': '/batch_confirm_purchase_order/batch_confirm_purchase_order',
#             'objects': http.request.env['batch_confirm_purchase_order.batch_confirm_purchase_order'].search([]),
#         })

#     @http.route('/batch_confirm_purchase_order/batch_confirm_purchase_order/objects/<model("batch_confirm_purchase_order.batch_confirm_purchase_order"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('batch_confirm_purchase_order.object', {
#             'object': obj
#         })