from odoo import api, fields, models, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)

class InstallmentsPayment(models.Model):
    _name = 'installments.payment'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = 'Installments Payment'
    _order = 'create_date desc, id desc'

    def _default_currency_id(self):
        company_id = self.env.context.get('force_company') or self.env.context.get('company_id') or self.env.user.company_id.id
        return self.env['res.company'].browse(company_id).currency_id
    
    @api.model
    def create(self, vals):
        company_id = vals.get('company_id', self.default_get(['company_id'])['company_id'])
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].with_context(force_company=company_id).next_by_code('installments.payment') or '/'
        
        if vals['type'] == 'leasing':
            vals['journal_id'] = self.env.user.company_id.journal_leasing_id.id
        return super(InstallmentsPayment, self.with_context(company_id=company_id)).create(vals)

    @api.depends('main_debt', 'line_ids.state')
    def _compute_remaining(self):
        for doc in self:
            paid_off = 0
            for line in doc.line_ids:
                if line.state != 'open':
                    paid_off += doc.installments
            
            doc.update({ 'remaining': doc.main_debt - paid_off })

    @api.depends('total_amount', 'down_payment')
    def _compute_main_debt(self):
        for doc in self:
            doc.update({ 'main_debt': doc.total_amount - doc.down_payment })

    @api.onchange('type')
    def _onchange_type(self):
        if self.type == 'leasing':
            self.journal_id = self.env.user.company_id.journal_leasing_id.id
        if self.type == 'bank':
            self.journal_id = False

    name = fields.Char('Name', required=True, copy=False, index=True, default=lambda self: _('New'))
    description = fields.Char('Description', required=True)
    asset = fields.Char('Asset', required=True)
    payment_date = fields.Date('Payment Date', required=True)
    
    total_amount = fields.Monetary('Total', required=True)
    down_payment = fields.Monetary('Down Payment', required=True)
    main_debt = fields.Monetary('Main Debt', compute="_compute_main_debt", store=True, readonly=True)
    tenor = fields.Integer('Tenor (Month)', required=True)
    
    interest_type = fields.Selection([
        ('annuity', 'Annuity'),
        ('flat', 'Flat'),
        ('decreased', 'Decreased'),
    ], string='Interest Type', required=True, default='annuity')
    interest = fields.Float('Interest', required=True)

    remaining = fields.Monetary('Remaining Installments', compute='_compute_remaining', store=True)
    journal_id = fields.Many2one('account.journal', string='Journal', required=True)
    move_id = fields.Many2one('account.move', string='Journal Entry')
    
    installments = fields.Monetary('Installment', readonly=True)
    installments_corr = fields.Monetary('Installment Corr', required=True)
    
    create_date = fields.Datetime(string='Creation Date', index=True, help="Date on which installments payment is created.")
    confirmation_date = fields.Datetime(string='Approved Date', index=True, help="Date on which the installments payment is confirmed.", copy=False)
    
    user_id = fields.Many2one('res.users', string='Submitter', index=True, track_visibility='onchange', track_sequence=2, default=lambda self: self.env.user)
    approver_id = fields.Many2one('res.users', string='Approver', index=True, track_visibility='onchange', track_sequence=2)
    currency_id = fields.Many2one("res.currency", string="Currency", readonly=True, required=True, default=_default_currency_id)
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, readonly=True, default=lambda self: self.env.user.company_id.id)
    
    line_ids = fields.One2many('installments.payment.line', 'doc_id', string='Payment Lines', copy=False)
    type = fields.Selection([
        ('bank', 'Bank'),
        ('leasing', 'Leasing'),
    ], string='Type', default='leasing', required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='State', default='draft')

    # additional
    next_payment_date = fields.Date('Next Payment Date')

    @api.multi
    def unlink(self):
        for order in self:
            if order.state not in ('draft', 'cancel'):
                raise UserError(_('You can not delete confirmed installments. You must first cancel it.'))
        return super(InstallmentsPayment, self).unlink()

    @api.multi
    def print_doc(self):
        return self.env.ref('installments_payment.action_report_installments_payment')\
            .with_context(discard_logo_check=True).report_action(self)

    @api.multi
    def action_draft(self):
        orders = self.filtered(lambda s: s.state in ['cancel'])
        return orders.write({
            'state': 'draft',
            'confirmation_date': False,
            'approver_id': False
        })
    
    @api.multi
    def action_approve(self):
        for doc in self:
            AccountMove = self.env['account.move']
            if doc._get_forbidden_state_approve() & set(doc.mapped('state')):
                raise UserError(_(
                    'It is not allowed to approve an installments in the following states: %s'
                ) % (', '.join(doc._get_forbidden_state_approve())))
            
            # create journal
            journal = self.journal_id
            if doc.type == 'bank':
                acc_credit = self.env.user.company_id.account_bank_debt_id
                acc_debit = journal.default_debit_account_id
            else:
                acc_credit = journal.default_credit_account_id
                acc_debit = self.env.user.company_id.account_asset_debt_id

            credit_line = {
                'account_id': acc_credit.id,
                'name': acc_credit.name,
                'debit': 0,
                'credit': doc.main_debt,
            }
            debit_line = {
                'account_id': acc_debit.id,
                'name': acc_debit.name,
                'debit': doc.main_debt,
                'credit': 0,
            }
            move = AccountMove.create({
                'date': fields.Date.today(), #?
                'journal_id': journal.id,
                'ref': doc.name,
                # 'state': 'posted',
                'name': doc.name,
                'company_id': self.env.user.company_id.id,
                'line_ids': [(0, 0, debit_line), (0, 0, credit_line)]
            })
            move.action_post()
            doc.write({ 'move_id': move.id })

            doc.write({
                'state': 'approved',
                'confirmation_date': fields.Datetime.now(),
                'approver_id': self.env.user.id,
            })

    @api.multi
    def action_cancel(self):
        for doc in self:
            if doc.state != 'draft':
                raise UserError(_("Can't cancel installment, because the payment is in progress or done!"))
            
            for line in doc.line_ids:
                if line.state != 'open':
                    raise UserError(_("Can't cancel installment, because the payment is in progress!"))
                
            return doc.write({
                'state': 'cancel',
                'confirmation_date': False,
                'approver_id': False
            })
    
    def _get_forbidden_state_approve(self):
        return {'done', 'cancel'}
    
    @api.multi
    def compute_installments(self):
        for doc in self:
            interest = 0
            
            doc.unlink_line_ids()

            main_debt = doc.main_debt
            payment_date = datetime.strptime(str(self.payment_date), '%Y-%m-%d')
            

            for line in range(1, self.tenor+1):
                interest = main_debt*doc.interest/1200
                self.env['installments.payment.line'].create({
                    'doc_id': doc.id,
                    'name': 'Installments to ' + str(line) + ' of ' + str(self.tenor),
                    'order': line,
                    'interest': interest,
                    'main_debt': doc.installments - interest,
                    'amount': doc.installments,
                    'payment_date': payment_date,
                    'state': 'open',
                })
                
                main_debt = main_debt - (doc.installments - interest)
                payment_date = payment_date + relativedelta(months=1)
    
    def unlink_line_ids(self):
        line_paid_off = self.env['installments.payment.line'].search([
            ('doc_id.id', '=', self.id),
            ('state', '!=', 'open'),
        ])
        if line_paid_off: 
            raise UserError(_("Can't unlink line payment!"))
        
        for line in self.line_ids:
            line.unlink()
    
    @api.multi
    def write(self, values):
        if 'tenor' in values or 'payment_date' in values:
            if self.state != 'draft':
                raise UserError(_("can't change value of tenor and payment date!"))
            
        return super(InstallmentsPayment, self).write(values)

    def compute_remaining(self):
        paid_off = 0
        for line in self.line_ids:
            if line.state != 'open':
                paid_off += self.installment

        remaining = self.main_debt - paid_off
        self.write({ 'remaining': remaining })

    def calculate(self):
        if self.interest_type == 'annuity':
            if self.main_debt > 0 and self.interest > 0 and self.tenor > 0:
                installments = self.main_debt * (self.interest/1200)/(1-((1+(self.interest/1200))**(self.tenor*-1)))
                self.write({ 'installments': installments, 'installments_corr': installments })

    def process_back(self):
        next_pay = self.env['installments.payment.line'].search([ ('next_payment', '=', True), ('doc_id.id', '=', self.id) ])
        if next_pay:
            order = next_pay.order
            lines = self.env['installments.payment.line'].search([ ('order', '<', order), ('doc_id.id', '=', self.id) ])
            for line in lines:
                line.write({ 'state': 'paid' })
            lines = self.env['installments.payment.line'].search([ ('order', '>=', order), ('doc_id.id', '=', self.id) ])
            for line in lines:
                line.write({ 'state': 'open' })

class InstallmentsPaymentLine(models.Model):
    _name = 'installments.payment.line'

    def _default_currency_id(self):
        company_id = self.env.context.get('force_company') or self.env.context.get('company_id') or self.env.user.company_id.id
        return self.env['res.company'].browse(company_id).currency_id

    doc_id = fields.Many2one('installments.payment', string='Doc Reference', required=True, ondelete='cascade', index=True, copy=False)
    name = fields.Char('Description', required=True)
    
    order = fields.Integer('Order', required=True)

    interest = fields.Monetary('Interest', required=True)
    main_debt = fields.Monetary('Main Debt', required=True)
    amount = fields.Monetary('Amount', required=True)
    
    payment_date = fields.Date('Deadline', required=True)
    state = fields.Selection([
        ('open', 'Open'),
        ('paid', 'Paid'),
    ], string='State', required=True, default='open')
    journal_id = fields.Many2one('account.move', string='Journal Entry', readonly=True)
    next_payment = fields.Boolean('Next', default=False)
    
    currency_id = fields.Many2one("res.currency", string="Currency", readonly=True, required=True, default=_default_currency_id)
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, readonly=True, default=lambda self: self.env.user.company_id.id)

    def name_get(self):
        res = []
        for rec in self:
            doc_name = rec.doc_id.asset or rec.doc_id.name
            res.append((rec.id, doc_name + ", Angsuran " + str(rec.order) + '/' + str(rec.doc_id.tenor) ))
        
        return res