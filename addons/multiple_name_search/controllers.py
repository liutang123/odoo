# -*- coding: utf-8 -*-
from openerp import http

# class MultipleNameSearch(http.Controller):
#     @http.route('/multiple_name_search/multiple_name_search/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/multiple_name_search/multiple_name_search/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('multiple_name_search.listing', {
#             'root': '/multiple_name_search/multiple_name_search',
#             'objects': http.request.env['multiple_name_search.multiple_name_search'].search([]),
#         })

#     @http.route('/multiple_name_search/multiple_name_search/objects/<model("multiple_name_search.multiple_name_search"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('multiple_name_search.object', {
#             'object': obj
#         })