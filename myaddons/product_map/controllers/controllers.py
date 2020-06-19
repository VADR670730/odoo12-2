# -*- coding: utf-8 -*-
from odoo import http

# class ProductMap(http.Controller):
#     @http.route('/product_map/product_map/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/product_map/product_map/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('product_map.listing', {
#             'root': '/product_map/product_map',
#             'objects': http.request.env['product_map.product_map'].search([]),
#         })

#     @http.route('/product_map/product_map/objects/<model("product_map.product_map"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('product_map.object', {
#             'object': obj
#         })