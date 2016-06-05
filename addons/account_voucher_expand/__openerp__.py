# -*- coding: utf-8 -*-
{
    'name': "account_voucher_expand",

    'summary': """
        Add Receivable/Payable movement offset method for voucher.""",

    'description': """
        收款时，可选择应收应付的凭证行进行对结。
    """,

    'author': "Nicho",
    'website': "http://www.bjut.edu.cn",

    'category': 'Account',
    'version': '0.1',

    'depends': ['base', 'account_voucher'],

    'data': [
        # 'security/ir.model.access.csv',
        # 'templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo.xml',
    ],
}