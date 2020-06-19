# -*- coding: utf-8 -*-
from odoo import http

# class AddAmountDifference(http.Controller):
#     @http.route('/add_amount_difference/add_amount_difference/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/add_amount_difference/add_amount_difference/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('add_amount_difference.listing', {
#             'root': '/add_amount_difference/add_amount_difference',
#             'objects': http.request.env['add_amount_difference.add_amount_difference'].search([]),
#         })

#     @http.route('/add_amount_difference/add_amount_difference/objects/<model("add_amount_difference.add_amount_difference"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('add_amount_difference.object', {
#             'object': obj
#         })