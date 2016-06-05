# -*- coding: utf-8 -*-
from openerp import http

# class AccountVoucherExpand(http.Controller):
#     @http.route('/account_voucher_expand/account_voucher_expand/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/account_voucher_expand/account_voucher_expand/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('account_voucher_expand.listing', {
#             'root': '/account_voucher_expand/account_voucher_expand',
#             'objects': http.request.env['account_voucher_expand.account_voucher_expand'].search([]),
#         })

#     @http.route('/account_voucher_expand/account_voucher_expand/objects/<model("account_voucher_expand.account_voucher_expand"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('account_voucher_expand.object', {
#             'object': obj
#         })