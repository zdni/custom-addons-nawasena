from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError
from odoo.tools.float_utils import float_compare

import logging
_logger = logging.getLogger(__name__)

class PaymentRequest(models.Model):
    _name = 'payment.request'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = 'Payment Request'

    def _default_currency_id(self):
        company_id = self.env.context.get('force_company') or self.env.context.get('company_id') or self.env.user.company_id.id
        return self.env['res.company'].browse(company_id).currency_id

    @api.depends('line_ids.state', 'line_ids.amount')
    def _compute_remaining(self):
        for doc in self:
            total = 0
            for line in doc.line_ids:
                if line.state == 'open':
                    total += line.amount
            
            doc.update({ 'remaining_amount': total })

    @api.depends('line_ids.amount')
    def _amount_all(self):
        for request in self:
            amount_total = 0
            for line in request.line_ids:
                if not line.state == 'paid': amount_total += line.amount
            
            request.update({ 'amount_total': amount_total })

    name = fields.Char('Name', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New Payment Request'))
    create_date = fields.Datetime(string='Creation Date', readonly=True, index=True, help="Date on which payment request is created.")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='State', default='draft')
    line_ids = fields.One2many('payment.request.line', 'payment_id', string='Payment Lines', states={'draft': [('readonly', False)]}, copy=True, readonly=True)

    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all')
    remaining_amount = fields.Monetary('Remaining Amount', readonly=True, compute='_compute_remaining', store=True)

    payment_journal_id = fields.Many2one('account.journal', string='Journal', domain=[('type', 'in', ['bank', 'cash'])])
    payment_date = fields.Date('Payment Date')

    user_id = fields.Many2one('res.users', string='Payment Submitter', index=True, track_visibility='onchange', default=lambda self: self.env.user)
    approver_id = fields.Many2one('res.users', string='Approver', index=True, track_visibility='onchange', track_sequence=2, readonly=True)
    currency_id = fields.Many2one("res.currency", string="Currency", readonly=True, required=True, default=_default_currency_id)
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, readonly=True, default=lambda self: self.env.user.company_id.id)

    @api.model
    def create(self, vals):
        company_id = vals.get('company_id', self.default_get(['company_id'])['company_id'])
        if vals.get('name', 'New Payment Request') == 'New Payment Request':
            vals['name'] = self.env['ir.sequence'].with_context(force_company=company_id).next_by_code('payment.request') or '/'
        return super(PaymentRequest, self.with_context(company_id=company_id)).create(vals)

    @api.multi
    def unlink(self):
        for request in self:
            if not request.state == 'cancel':
                raise UserError(_('In request to delete a payment request, you must cancel it first.'))
            
        return super(PaymentRequest, self).unlink()
    
    @api.multi
    def print_doc(self):
        return self.env.ref('payment_request.report_payment_request').report_action(self)

    @api.multi
    def action_draft(self):
        orders = self.filtered(lambda s: s.state in ['cancel'])
        return orders.write({
            'state': 'draft',
            'approver_id': False
        })
    
    @api.multi
    def action_approve(self):
        if self._get_forbidden_state_approve() & set(self.mapped('state')):
            raise UserError(_(
                'It is not allowed to approve an installments in the following states: %s'
            ) % (', '.join(self._get_forbidden_state_approve())))
        
        self.write({
            'state': 'approved',
            'approver_id': self.env.user.id
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
                'approver_id': False
            })
        
    @api.multi
    def action_done(self):
        for doc in self:
            pass
    
    def _get_forbidden_state_approve(self):
        return {'done', 'cancel'}

class PaymentRequestLine(models.Model):
    _name = 'payment.request.line'
    _description = 'Payment Request Line'

    @api.model
    def create(self, vals):
        if 'name' in vals and not vals['communication']:
            _logger.warning('create payment request')
            vals['communication'] = vals['name']
            
        return super(PaymentRequestLine, self).create(vals)

    def _default_currency_id(self):
        company_id = self.env.context.get('force_company') or self.env.context.get('company_id') or self.env.user.company_id.id
        return self.env['res.company'].browse(company_id).currency_id

    payment_id = fields.Many2one('payment.request', string='Payment Reference', required=True, ondelete='cascade', index=True, copy=False)
    name = fields.Char('Description', required=True, default=lambda self: _('New'))
    amount = fields.Monetary('Amount')
    state = fields.Selection([
        ('open', 'Open'),
        ('paid', 'Paid'),
    ], string='State', default='open', readonly=True)
    journal_id = fields.Many2one('account.journal', string='Journal', domain=[('type', 'in', ['bank', 'cash'])])
    payment_date = fields.Date('Payment Date')
    communication = fields.Char('Memo')
    move_id = fields.Many2one('account.move', string='Payment')

    currency_id = fields.Many2one("res.currency", string="Currency", readonly=True, required=True, default=_default_currency_id)
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, readonly=True, default=lambda self: self.env.user.company_id.id)

    @api.multi
    def unlink(self):
        for line in self:
            if not line.state == 'open' or not line.payment_id.state in ['draft', 'cancel']:
                raise UserError(_("Can't delete line payment request!"))
        return super(PaymentRequestLine, self).unlink()
    
