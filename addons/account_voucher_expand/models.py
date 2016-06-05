# -*- coding: utf-8 -*-

from openerp import models, fields, api

# 重写会计模块的AccountVoucher
class AccountVoucher(models.Model):
    _inherit = ['account.voucher']

    # 重新计算付款凭证行,在收款时，在借方可以显示应付科目，在付款时，在贷方可以显示应收科目
    # 覆盖了account_voucher模块中的account_voucher.py中account_voucher类的同名方法
    def recompute_voucher_lines(self, cr, uid, ids, partner_id, journal_id, price, currency_id, ttype, date, context=None):
        """
        返回一个包含新的context的字典
        @param partner_id: 用户最后一次指定的partner_id
        @param args: other arguments
        @param context: context arguments, like lang, time zone

        @return: Returns a dict which contains new values, and context
        """
        def _remove_noise_in_o2m():
            """if the line is partially reconciled, then we must pay attention to display it only once and
                in the good o2m.
                如果该凭证行被部分核销，则要保证关于该凭证行的核销所包含的所有凭证行只被显示一次。
                该方法在凭证行（line）为噪声的时候，返回True，表明该行不需要显示。
                同一核销下的凭证行，显示未核销金额大于0的凭证行。
                例如
                 应收时：
                     借：应收 100元
                     贷：应收 50元
                         应收 10元
                上面的核销代表向别人收取了两次款，一次50元，一次10元。则只有100元的凭证行的部分未付款为正。
                 应付时：
                     借：应付 20元
                         应付 30元
                     贷：应付 100元
                上面的核销代表向别人付款两次，一次20元，一次30元。则只有100元的凭证行的部分未付款为正
                去掉不应该对结的凭证行
            """
            if line.reconcile_partial_id:
                if currency_id == line.currency_id.id:
                    if line.amount_residual_currency <= 0:
                        return True
                else:
                    if line.amount_residual <= 0:
                        return True
                if ttype == 'payment'and line.account_id.type == 'receivable' and line.debit:
                    return True
                if ttype == 'receipt' and line.account_id.type == 'payable' and line.credit:
                    return True
            return False

        if context is None:
            context = {}
        context_multi_currency = context.copy()

        currency_pool = self.pool.get('res.currency')
        move_line_pool = self.pool.get('account.move.line')
        partner_pool = self.pool.get('res.partner')
        journal_pool = self.pool.get('account.journal')
        line_pool = self.pool.get('account.voucher.line')

        # set default values
        default = {
            'value': {'line_dr_ids': [], 'line_cr_ids': [], 'pre_line': False},
        }

        # drop existing lines
        line_ids = ids and line_pool.search(cr, uid, [('voucher_id', '=', ids[0])])
        for line in line_pool.browse(cr, uid, line_ids, context=context):
            if line.type == 'cr':
                default['value']['line_cr_ids'].append((2, line.id))
            else:
                default['value']['line_dr_ids'].append((2, line.id))

        if not partner_id or not journal_id:
            return default

        journal = journal_pool.browse(cr, uid, journal_id, context=context)
        partner = partner_pool.browse(cr, uid, partner_id, context=context)
        currency_id = currency_id or journal.company_id.currency_id.id

        total_credit = 0.0
        total_debit = 0.0
        account_type = None
        if context.get('account_id'):
            account_type = self.pool['account.account'].browse(cr, uid, context['account_id'], context=context).type
        if ttype == 'payment':
            total_debit = price or 0.0
        else:
            total_credit = price or 0.0
        type_search_domain = ['|', ('account_id.type', '=', 'receivable'), ('account_id.type', '=', 'payable')] if not account_type else [('account_id.type', '=', account_type)]

        if not context.get('move_line_ids', False):
            ids = move_line_pool.search(cr, uid,
                                        [('state', '=', 'valid'),
                                         ('reconcile_id', '=', False),
                                         ('partner_id', '=', partner_id),
                                         ] + type_search_domain,
                                        context=context)
        else:
            ids = context['move_line_ids']
        invoice_id = context.get('invoice_id', False)
        company_currency = journal.company_id.currency_id.id
        move_lines_found = []

        # order the lines by most old first
        ids.reverse()
        account_move_lines = move_line_pool.browse(cr, uid, ids, context=context)

        # compute the total debit/credit and look for a matching open amount or invoice
        for line in account_move_lines:
            if _remove_noise_in_o2m():
                continue

            if invoice_id:
                if line.invoice.id == invoice_id:
                    # if the invoice linked to the voucher line is equal to the invoice_id in context
                    # then we assign the amount on that line, whatever the other voucher lines
                    move_lines_found.append(line.id)
            elif currency_id == company_currency:
                # otherwise treatments is the same but with other field names
                if line.amount_residual == price:
                    # if the amount residual is equal the amount voucher, we assign it to that voucher
                    # line, whatever the other voucher lines
                    move_lines_found.append(line.id)
                    break
                # otherwise we will split the voucher amount on each line (by most old first)
                total_credit += line.credit or 0.0
                total_debit += line.debit or 0.0
            elif currency_id == line.currency_id.id:
                if line.amount_residual_currency == price:
                    move_lines_found.append(line.id)
                    break
                total_credit += line.credit and line.amount_currency or 0.0
                total_debit += line.debit and line.amount_currency or 0.0

        remaining_amount = price
        # voucher line creation
        for line in account_move_lines:

            if _remove_noise_in_o2m():
                continue

            if line.currency_id and currency_id == line.currency_id.id:
                amount_original = abs(line.amount_currency)
                amount_unreconciled = abs(line.amount_residual_currency)
            else:
                # always use the amount booked in the company currency
                # as the basis of the conversion into the voucher currency
                amount_original = currency_pool.compute(cr, uid, company_currency, currency_id, line.credit or
                                                        line.debit or 0.0, context=context_multi_currency)
                amount_unreconciled = currency_pool.compute(cr, uid, company_currency, currency_id,
                                                            abs(line.amount_residual), context=context_multi_currency)
            line_currency_id = line.currency_id and line.currency_id.id or company_currency
            rs = {
                'name': line.move_id.name,
                'type': line.credit and 'dr' or 'cr',
                'move_line_id': line.id,
                'account_id': line.account_id.id,
                'amount_original': amount_original,
                'amount': (line.id in move_lines_found) and min(abs(remaining_amount), amount_unreconciled) or 0.0,
                'date_original': line.date,
                'date_due': line.date_maturity,
                'amount_unreconciled': amount_unreconciled,
                'currency_id': line_currency_id,
            }
            remaining_amount -= rs['amount']
            # in case a corresponding move_line hasn't been found, we now try to assign the voucher amount
            # on existing invoices: we split voucher amount by most old first, but only for lines in the same currency
            if not move_lines_found:
                if currency_id == line_currency_id:
                    if line.credit:
                        amount = min(amount_unreconciled, abs(total_debit))
                        rs['amount'] = amount
                        total_debit -= amount
                    else:
                        amount = min(amount_unreconciled, abs(total_credit))
                        rs['amount'] = amount
                        total_credit -= amount

            if rs['amount_unreconciled'] == rs['amount']:
                rs['reconcile'] = True

            if rs['type'] == 'cr':
                default['value']['line_cr_ids'].append(rs)
            else:
                default['value']['line_dr_ids'].append(rs)

            if len(default['value']['line_cr_ids']) > 0 or len(default['value']['line_dr_ids']) > 0:
                default['value']['pre_line'] = 1
            default['value']['writeoff_amount'] = self._compute_writeoff_amount(cr, uid,
                                                                                default['value']['line_dr_ids'],
                                                                                default['value']['line_cr_ids'],
                                                                                price, ttype)
        return default
