from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError

import logging
_logger = logging.getLogger(__name__)

class PRInstallmentsPayment(models.Model):
    _name = 'pr.installments.payment'
    _inherit = ['payment.request', 'portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = 'Payment Request Installments'

    line_ids = fields.One2many('prl.installments.payment', 'payment_id', string='Installments Lines', states={'draft': [('readonly', False)]}, copy=True, readonly=True)

    start_date = fields.Date('Start Date', default=lambda self: fields.Date.today())
    end_date = fields.Date('End Date', default=lambda self: fields.Date.today())

    @api.multi
    def generate(self):
        for doc in self:
            if not doc.start_date or not doc.end_date:
                raise UserError(_("Set Start Date and End Date!"))

            for line in doc.line_ids: line.unlink()

            installments = self.env['installments.payment.line'].search([
                ('payment_date', '>=', doc.start_date),
                ('payment_date', '<=', doc.end_date),
                ('state', '=', 'open'),
                ('doc_id.state', '=', 'approved'),
            ])
            for installment in installments:
                self.env['prl.installments.payment'].create({
                    'payment_id': doc.id,
                    'installments_id': installment.id,
                    'amount': installment.main_debt,
                    'interest_amount': installment.interest,
                    'total_installments': installment.amount,
                })
                
    @api.multi
    def action_done(self):
        for doc in self:
            for line in doc.line_ids:
                if not line.journal_id:
                    raise UserError(_("Set Account Journal first!"))
                if not line.payment_date:
                    raise UserError(_("Set Payment Date first!"))
                
            AccountMove = self.env['account.move']
            journal_leasing = self.env.user.company_id.journal_leasing_id
            if not journal_leasing: raise UserError(_("Set Journal for Free Driver!"))
            
            for line in doc.line_ids:
                journal = line.journal_id

                if line.installments_id.doc_id.type == 'bank':
                    acc_debit = self.env.user.company_id.account_bank_debt_id
                else:
                    acc_debit = journal_leasing.default_credit_account_id

                line_ids = []
                
                credit_line = {
                    'account_id': journal.default_credit_account_id.id,
                    'name': journal.default_credit_account_id.name,
                    'debit': 0,
                    'credit': line.installments_id.doc_id.installments_corr,
                }
                line_ids.append((0, 0, credit_line))
                debit_line = {
                    'account_id': acc_debit.id,
                    'name': acc_debit.name,
                    'debit': line.amount,
                    'credit': 0,
                }
                line_ids.append((0, 0, debit_line))
                if line.interest_amount:
                    # interest debit
                    interest_line = {
                        'account_id': self.env.user.company_id.account_interest_debt_id.id,
                        'name': self.env.user.company_id.account_interest_debt_id.name,
                        'debit': line.interest_amount,
                        'credit': 0,
                    }
                    line_ids.append((0, 0, interest_line))

                if not line.total_installments == line.installments_id.doc_id.installments_corr:
                    debit = credit = 0
                    if line.total_installments > line.installments_id.doc_id.installments_corr:
                        credit = line.total_installments - line.installments_id.doc_id.installments_corr
                    else:
                        debit = line.installments_id.doc_id.installments_corr - line.total_installments 
                    # diff line
                    diff_line = {
                        'account_id': self.env.user.company_id.account_installments_diff_id.id,
                        'name': self.env.user.company_id.account_installments_diff_id.name,
                        'debit': debit,
                        'credit': credit,
                    }
                    line_ids.append((0, 0, diff_line))
                
                # create account move
                move = AccountMove.create({
                    'date': line.payment_date,
                    'journal_id': journal.id,
                    'ref': line.installments_id.doc_id.name + ', ' + line.installments_id.name,
                    'state': 'posted',
                    'name': doc.name,
                    'company_id': self.env.user.company_id.id,
                    'line_ids': line_ids,
                })
                
                line.write({ 
                    'move_id': move.id,
                    'state': 'paid',
                })
                
                next_pay = self.env['installments.payment.line'].search([ 
                    ('order', '=', (line.installments_id.order+1)),
                    ('doc_id.id', '=', line.installments_id.doc_id.id),
                ], limit=1)
                line.installments_id.write({ 
                    'journal_id': move.id,
                    'state': 'paid',
                })
                line.installments_id.doc_id.write({ 
                    'next_payment_date': next_pay.payment_date if next_pay else False,
                })
        
            doc.write({ 'state': 'done' })

    @api.multi
    def print_doc(self):
        return self.env.ref('installments_payment.action_report_pr_installments_payment')\
            .with_context(discard_logo_check=True).report_action(self)

    def apply_for_all_line(self):
        for line in self.line_ids:
            line.write({
                'journal_id': self.payment_journal_id.id,
                'payment_date': self.payment_date,
            })
    
    @api.depends('line_ids.state', 'line_ids.corr_amount')
    def _compute_remaining(self):
        for doc in self:
            total = 0
            for line in doc.line_ids:
                if line.state == 'open':
                    total += line.corr_amount
            doc.update({ 'remaining_amount': total })
    
class PRLInstallmentsPayment(models.Model):
    _name = 'prl.installments.payment'
    _description = 'Payment Request Line Installments'
    _inherit = 'payment.request.line'

    @api.depends('installments_id')
    def _count_amount(self):
        for doc in self:
            if doc.installments_id:
                installments = self.env['installments.payment.line'].search([ ('id', '=', doc.installments_id.id) ])
                if installments: doc.update({ 'amount': installments.main_debt })
    
    @api.depends('installments_id')
    def _count_corr_amount(self):
        for doc in self:
            if doc.installments_id:
                installments = self.env['installments.payment.line'].search([ ('id', '=', doc.installments_id.id) ])
                if installments: doc.update({ 'corr_amount': installments.doc_id.installments_corr })

    @api.depends('amount', 'interest_amount')
    def _count_total_installments(self):
        for doc in self:
            doc.update({ 'total_installments': doc.amount + doc.interest_amount })

    payment_id = fields.Many2one('pr.installments.payment', string='Payment Reference', required=True, ondelete='cascade', index=True, copy=False)
    installments_id = fields.Many2one('installments.payment.line', string='Source Document', required=True, ondelete='cascade', index=True, copy=False, domain=[('state', '=', 'open')])
    amount = fields.Monetary('Main Debt', compute='_count_amount', readonly=True, store=True)
    interest_amount = fields.Monetary('Interest', required=True)
    total_installments = fields.Monetary('Total Installments', compute='_count_total_installments', readonly=True, store=True)
    corr_amount = fields.Monetary('Corr Amount', compute='_count_corr_amount', readonly=True, store=True)


    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            installments = self.env['installments.payment.line'].search([ ('id', '=', vals['installments_id']) ], limit=1)
            vals['name'] = installments.name or '/'
            vals['communication'] = installments.doc_id.name
            
        return super(PRLInstallmentsPayment, self).create(vals)
