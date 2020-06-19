# -*- coding: utf-8 -*-
from odoo import http

# class CustomsInterface(http.Controller):
#     @http.route('/customs_interface/customs_interface/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/customs_interface/customs_interface/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('customs_interface.listing', {
#             'root': '/customs_interface/customs_interface',
#             'objects': http.request.env['customs_interface.customs_interface'].search([]),
#         })

#     @http.route('/customs_interface/customs_interface/objects/<model("customs_interface.customs_interface"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('customs_interface.object', {
#             'object': obj
#         })