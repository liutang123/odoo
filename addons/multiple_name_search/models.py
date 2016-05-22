# -*- coding: utf-8 -*-
import re

from openerp import models, fields, api
from openerp.osv.expression import get_unaccent_wrapper, NEGATIVE_TERM_OPERATORS

from pinyin import PinYin
han2py = PinYin()
han2py.load_word()
# class multiple_name_search(models.Model):
#     _name = 'multiple_name_search.multiple_name_search'

#     name = fields.Char()

# 将name转化为拼音的公共方法
def comman_change_name(name):
    pinyinStr, pyStr = False, False
    if name: #如果有name
        
        pinyinArr = han2py.str2pinyin(name)
        print pinyinArr
        pyStr = ''.join([p[0] for p in pinyinArr])
        pinyinStr = ''.join(pinyinArr)
    return {'pinyin': pinyinStr, 'py': pyStr}

class WithPinyinProductTemplate(models.Model):
    _inherit = 'product.template'
    
    pinyin = fields.Char(string='拼音', help='拼音英语表示,如“名称”的拼音是“mingcheng”') # , default=lambda self: comman_change_name(self.name)['pinyin']
    py = fields.Char(string='拼音首字母', index=True, help='拼音英语表示首字母,如“名称”的拼音是“mingcheng”,则它的拼音首字母则为“mc”') # , default=lambda self: comman_change_name(self.name)['py']
    
    def _default_pinyin(self):
        return comman_change_name()
    
    def onchange_name(self, cr, uid, ids, name, context=None):
        """该方法返回产品的拼音（pinyin）和拼音简拼（py）
           :param name: ignored
        """
        return {'value': comman_change_name(name)}
    
# 真正的仓库和其他买卖单据中都保存的是产品规格，产品规格继承了产品模版，因此给产品模版添加了pinyin和py字段，则产品规格不用再次添加只需要实现其name_search即可
class WithPinyinProduct(models.Model):
    _inherit = 'product.product'
    
    # 重写name_search方法，使其可以支持拼音简称和拼音的查询
    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        if name:
            positive_operators = ['=', 'ilike', '=ilike', 'like', '=like']
            ids = []
            if operator in positive_operators:
                ids = self.search(cr, user, [('default_code','=',name)]+ args, limit=limit, context=context) # 首先查看内部编码是否符合
                if not ids:
                    ids = self.search(cr, user, [('ean13','=',name)]+ args, limit=limit, context=context) # 然后查看ean13编码是否符合
            # 如果查不到准确的内部编码和ean13编码所对应的商品
            # 如果不是反向查询操作（'!=', 'not like', 'not ilike', 'not in'）
            if not ids and operator not in NEGATIVE_TERM_OPERATORS:
                # 不要将下边的几个查询合并成一个查询，如果数千商品匹配，则SQL查询的性能会变的很差。
                # 由于处理巨量的合并和唯一需要OR操作（鉴于通过'name'属性的查找结果来自ir.translation表这一事实）
                # 在Python中进行合并会有更好的效率。
                ids = self.search(cr, user, args + [('default_code', operator, name)], limit=limit, context=context)
                if not limit or len(ids) < limit:
                    # we may underrun the limit because of dupes in the results, that's fine
                    limit2 = (limit - len(ids)) if limit else False
                    ids += self.search(cr, user, args + [('py', operator, name), ('id', 'not in', ids)], limit=limit2, context=context)
                if not limit or len(ids) < limit:
                    limit2 = (limit - len(ids)) if limit else False
                    ids += self.search(cr, user, args + [('pinyin', operator, name), ('id', 'not in', ids)], limit=limit2, context=context)
                if not limit or len(ids) < limit:
                    limit2 = (limit - len(ids)) if limit else False
                    ids += self.search(cr, user, args + [('name', operator, name), ('id', 'not in', ids)], limit=limit2, context=context)
            elif not ids and operator in NEGATIVE_TERM_OPERATORS:
                ids = self.search(cr, user, args + ['&', '&', '&', ('default_code', operator, name), \
                                                    ('py', operator, name), ('pinyin', operator, name), \
                                                    ('name', operator, name)], limit=limit, context=context)
            if not ids and operator in positive_operators:
                ptrn = re.compile('(\[(.*?)\])')
                res = ptrn.search(name)
                if res:
                    ids = self.search(cr, user, [('default_code','=', res.group(2))] + args, limit=limit, context=context)
        else:
            ids = self.search(cr, user, args, limit=limit, context=context)
        result = self.name_get(cr, user, ids, context=context)
        return result
    
class WithPinyinPartner(models.Model):
    _inherit = 'res.partner'
    
    pinyin = fields.Char(string='拼音', help='拼音英语表示,如“名称”的拼音是“mingcheng”')
    py = fields.Char(string='拼音首字母', index=True, help='拼音英语表示首字母,如“名称”的拼音是“mingcheng”,则它的拼音首字母则为“mc”')
    
    # 重新写name_search方法，不光要查询name匹配的数据，还要查询pinyin和py匹配的数据。
    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        if name and operator in ('=', 'ilike', '=ilike', 'like', '=like'):

            self.check_access_rights(cr, uid, 'read') # 产看当前用户是否有对res.partner的读权限
            where_query = self._where_calc(cr, uid, args, context=context)
            self._apply_ir_rules(cr, uid, where_query, 'read', context=context)
            from_clause, where_clause, where_clause_params = where_query.get_sql()
            where_str = where_clause and (" WHERE %s AND " % where_clause) or ' WHERE '

            # search on the name of the contacts and of its company
            search_name = name
            if operator in ('ilike', 'like'):
                search_name = '%%%s%%' % name
            if operator in ('=ilike', '=like'):
                operator = operator[1:]

            unaccent = get_unaccent_wrapper(cr)

            query = """SELECT id
                         FROM res_partner
                      {where} ({email} {operator} {percent}
                           OR {display_name} {operator} {percent}
                           OR {py} {operator} {percent}
                           OR {pinyin} {operator} {percent})
                     ORDER BY {display_name}
                    """.format(where=where_str, operator=operator,
                               email=unaccent('email'),
                               display_name=unaccent('display_name'),
                               py=unaccent('py'),
                               pinyin=unaccent('pinyin'),
                               percent=unaccent('%s'))

            where_clause_params += [search_name, search_name, search_name, search_name]
            if limit:
                query += ' limit %s'
                where_clause_params.append(limit)
            cr.execute(query, where_clause_params)
            ids = map(lambda x: x[0], cr.fetchall())

            if ids:
                return self.name_get(cr, uid, ids, context) # 根据一个partner所属国家的address格式对该partner的名称进行格式化
            else:
                return []
        return super(WithPinyinPartner,self).name_search(cr, uid, name, args, operator=operator, context=context, limit=limit)
    
    def onchange_name(self, cr, uid, ids, name, context=None):
        """该方法返回产品的拼音（pinyin）和拼音简拼（py）
           :param name: ignored
        """
        return {'value': comman_change_name(name)}
