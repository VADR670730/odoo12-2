# -*- coding: utf-8 -*-
from odoo import http

# class ReturnModel(http.Controller):
#     @http.route('/return_model/return_model/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/return_model/return_model/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('return_model.listing', {
#             'root': '/return_model/return_model',
#             'objects': http.request.env['return_model.return_model'].search([]),
#         })

#     @http.route('/return_model/return_model/objects/<model("return_model.return_model"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('return_model.object', {
#             'object': obj
#         })