# -*- coding: utf-8 -*-
# from odoo import http
#
# # class Dezs(http.Controller):
# #     @http.route('/dezs/dezs/', auth='public')
# #     def index(self, **kw):
# #         return "Hello, world"
#
# #     @http.route('/dezs/dezs/objects/', auth='public')
# #     def list(self, **kw):
# #         return http.request.render('dezs.listing', {
# #             'root': '/dezs/dezs',
# #             'objects': http.request.env['dezs.dezs'].search([]),
# #         })
#
# #     @http.route('/dezs/dezs/objects/<model("dezs.dezs"):obj>/', auth='public')
# #     def object(self, obj, **kw):
# #         return http.request.render('dezs.object', {
# #             'object': obj
# #         })