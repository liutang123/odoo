# -*- coding: utf-8 -*-
{
    'name': "Multiple Name Search",

    'summary': """给产品(product.product)和合作伙伴(res.partner)添加中文拼音和拼音首字母的查询功能""",

    'description': """
        新建采购单或编辑采购单时，供应商搜索按名称，拼音简写和拼音三个字段搜索
        新建销售单或编辑销售单时，客户搜索按名称，拼音简写和拼音三个字段搜索
        采购单，销售单中的商品按照拼音简写和拼音进行搜索
        TODO：在客户列表和产品列表按名称进行搜索时，按名称，拼音简写和拼音三个字段搜索
    """,

    'author': "zdhy 中达恒业",
    'website': "http://www.zhongdait.com/",

    'category': 'Localization',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','sale','purchase'],

    'data': [
        # 'security/ir.model.access.csv',
        'view/partner_view.xml',
        'view/product_view.xml',
    ],
    'demo': [
        #'demo.xml',
    ],
    'license': 'GPL-3',
    'auto_install': False,
    'installable': True,
}