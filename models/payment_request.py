from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError
from werkzeug import url_encode

import logging
_logger = logging.getLogger(__name__)

class PRExpense(models.Model):
    _name = 'pr.expense'
    _inherit = ['payment.request', 'portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = 'Payment Request Expense'

    line_ids = fields.One2many('prl.expense', 'payment_id', string='Expense Lines', states={'draft': [('readonly', False)]}, copy=True, readonly=True)

    start_date = fields.Date('Start Date', default=lambda self: fields.Date.today())
    end_date = fields.Date('End Date', default=lambda self: fields.Date.today())

    @api.multi
    def generate(self):
        for doc in self:
            if not doc.start_date or not doc.end_date:
                raise UserError(_("Set Start Date and End Date!"))

            for line in doc.line_ids: line.unlink()

            sheets = self.env['hr.expense'].search([
                ('date', '>=', doc.start_date),
                ('date', '<=', doc.end_date),
                ('state', '=', 'reported'),
            ])
            for sheet in sheets:
                journal_id = False if sheet.payment_mode == 'own_account' else sheet.sheet_id.bank_journal_id.id
                self.env['prl.expense'].create({
                    'payment_id': doc.id,
                    'sheet_id': sheet.sheet_id.id,
                    'amount': sheet.sheet_id.total_amount,
                    'journal_id': journal_id,
                })
                
    @api.multi
    def action_done(self):
        for doc in self:
            for line in doc.line_ids:
                sheet = line.sheet_id
                sheet.approve_expense_sheets()
                if sheet.payment_mode == 'company_account':
                    sheet.write({
                        'bank_journal_id': line.journal_id.id,
                        'accounting_date': line.payment_date
                    })
                line.sheet_id.action_sheet_move_create()
                if sheet.payment_mode == 'own_account':
                    self.payment_expense(line)

                line.write({ 'state': 'paid' })
                
            doc.write({ 'state': 'done' })

    def payment_expense(self, line):
        sheet = line.sheet_id
        partner_id = sheet.address_id.id or sheet.employee_id.id and sheet.employee_id.address_home_id.id
        payment_methods = line.journal_id.outbound_payment_method_ids
        payment_method_id = payment_methods and payment_methods[0] or False
        
        payment = self.env['account.payment'].create({
            'partner_type': 'supplier',
            'payment_type': 'outbound',
            'partner_id': partner_id,
            'journal_id': line.journal_id.id,
            'company_id': line.journal_id.company_id.id,
            'payment_method_id': payment_method_id.id,
            'amount': line.amount,
            'currency_id': line.currency_id.id,
            'payment_date': line.payment_date,
            'communication': ''
        })
        payment.post()

        # Log the payment in the chatter
        body = (_("A payment of %s %s with the reference <a href='/mail/view?%s'>%s</a> related to your expense %s has been made.") % (payment.amount, payment.currency_id.symbol, url_encode({'model': 'account.payment', 'res_id': payment.id}), payment.name, sheet.name))
        sheet.message_post(body=body)

        # Reconcile the payment and the expense, i.e. lookup on the payable account move lines
        account_move_lines_to_reconcile = self.env['account.move.line']
        for line in payment.move_line_ids + sheet.account_move_id.line_ids:
            if line.account_id.internal_type == 'payable' and not line.reconciled:
                account_move_lines_to_reconcile |= line
        account_move_lines_to_reconcile.reconcile()

    @api.multi
    def print_doc(self):
        return self.env.ref('pr_expenses.action_report_pr_expenses')\
            .with_context(discard_logo_check=True).report_action(self)

    def apply_for_all_line(self):
        for line in self.line_ids:
            line.write({
                'journal_id': self.payment_journal_id.id,
                'payment_date': self.payment_date,
            })
    
class PRLExpense(models.Model):
    _name = 'prl.expense'
    _description = 'Payment Request Line Expense'

    @api.depends('sheet_id')
    def _count_amount(self):
        for doc in self:
            if doc.sheet_id:
                sheet = self.env['hr.expense.sheet'].search([ ('id', '=', doc.sheet_id.id) ])
                if sheet: doc.update({ 'amount': sheet.total_amount })

    def _default_currency_id(self):
        company_id = self.env.context.get('force_company') or self.env.context.get('company_id') or self.env.user.company_id.id
        return self.env['res.company'].browse(company_id).currency_id

    name = fields.Char('Description', required=True, default=lambda self: _('New'))
    payment_id = fields.Many2one('pr.expense', string='Payment Reference', required=True, ondelete='cascade', index=True, copy=False)
    sheet_id = fields.Many2one('hr.expense.sheet', string='Source Document', required=True, ondelete='cascade', index=True, copy=False, domain=[('state', '=', 'approve')])
    amount = fields.Monetary('Amount', compute='_count_amount', readonly=True, store=True)
    state = fields.Selection([
        ('open', 'Open'),
        ('paid', 'Paid'),
    ], string='State', default='open', readonly=True)
    journal_id = fields.Many2one('account.journal', string='Journal', domain=[('type', 'in', ['bank', 'cash'])])
    payment_date = fields.Date('Payment Date')

    currency_id = fields.Many2one("res.currency", string="Currency", readonly=True, required=True, default=_default_currency_id)
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, readonly=True, default=lambda self: self.env.user.company_id.id)

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            sheet = self.env['hr.expense.sheet'].search([ ('id', '=', vals['sheet_id']) ], limit=1)
            vals['name'] = sheet.name + ', ' + (sheet.expense_line_ids[0].date.strftime('%d/%m/%Y') or '') or '/'
            
        return super(PRLExpense, self).create(vals)
    
    @api.multi
    def unlink(self):
        for line in self:
            if not line.state == 'open' or not line.payment_id.state in ['draft', 'cancel']:
                raise UserError(_("Can't delete line payment request!"))
        return super(PRLExpense, self).unlink()
