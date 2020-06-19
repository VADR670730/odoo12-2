# -*- coding: utf-8 -*-
from odoo import http

# class SalerOrderDeliverReport(http.Controller):
#     @http.route('/alter_invocice_deliver_report/alter_invocice_deliver_report/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/alter_invocice_deliver_report/alter_invocice_deliver_report/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('alter_invocice_deliver_report.listing', {
#             'root': '/alter_invocice_deliver_report/alter_invocice_deliver_report',
#             'objects': http.request.env['alter_invocice_deliver_report.alter_invocice_deliver_report'].search([]),
#         })

#     @http.route('/alter_invocice_deliver_report/alter_invocice_deliver_report/objects/<model("alter_invocice_deliver_report.alter_invocice_deliver_report"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('alter_invocice_deliver_report.object', {
#             'object': obj
#         })