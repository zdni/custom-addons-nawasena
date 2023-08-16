from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError

import logging
_logger = logging.getLogger(__name__)

class PRFeeDriver(models.Model):
    _name = 'pr.fee.driver'
    _inherit = ['payment.request', 'portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = 'Payment Request Fee Driver'
    
    line_ids = fields.One2many('prl.fee.driver', 'payment_id', string='Fee Lines', states={'draft': [('readonly', False)]}, copy=True, readonly=True)

    start_date = fields.Date('Start Date', default=lambda self: fields.Date.today())
    end_date = fields.Date('End Date', default=lambda self: fields.Date.today())

    @api.multi
    def generate_fee(self):
        for doc in self:
            if not doc.start_date or not doc.end_date:
                raise UserError(_("Set Start Date and End Date!"))

            for line in doc.line_ids: line.unlink()

            fees = self.env['fee.driver.line'].search([
                ('fee_id.delivery_date', '>=', doc.start_date),
                ('fee_id.delivery_date', '<=', doc.end_date),
                ('state', '=', 'open'),
                ('fee_id.state', '=', 'posted'),
            ], order='driver_id ASC, delivery_date ASC')
            for fee in fees:
                self.env['prl.fee.driver'].create({
                    'payment_id': doc.id,
                    'fee_id': fee.id,
                    'amount': fee.amount
                })
                
    @api.multi
    def action_done(self):
        for doc in self:
            for line in doc.line_ids:
                if not line.journal_id:
                    raise UserError(_("Set Account Journal first!"))
                
            AccountMove = self.env['account.move']
            journal_fee = self.env.user.company_id.journal_fee_driver_id
            if not journal_fee: raise UserError(_("Set Journal for Free Driver!"))
            
            for line in doc.line_ids:
                journal = line.journal_id

                credit_line = {
                    'account_id': journal.default_credit_account_id.id,
                    'name': journal.default_credit_account_id.name,
                    'debit': 0,
                    'credit': line.amount,
                }
                debit_line = {
                    'account_id': journal_fee.default_credit_account_id.id,
                    'name': journal_fee.default_credit_account_id.name,
                    'debit': line.amount,
                    'credit': 0,
                }
                # create account move
                move = AccountMove.create({
                    'date': line.payment_date,
                    'journal_id': journal.id,
                    'ref': line.fee_id.fee_id.name + ', ' + line.fee_id.name,
                    'state': 'posted',
                    'name': doc.name,
                    'company_id': self.env.user.company_id.id,
                    'line_ids': [(0, 0, debit_line), (0, 0, credit_line)]
                })
                
                line.write({ 
                    'move_id': move.id,
                    'state': 'paid',
                })
                line.fee_id.write({ 
                    'journal_id': move.id,
                    'state': 'paid',
                })
        
            doc.write({ 'state': 'done' })
    
    @api.multi
    def action_recalculate(self):
        for doc in self:
            for line in doc.line_ids:
                line.write({ 'amount': line.fee_id.amount })

    @api.multi
    def print_doc(self):
        return self.env.ref('fee_driver.action_report_pr_fee_driver')\
            .with_context(discard_logo_check=True).report_action(self)

    def apply_for_all_line(self):
        for line in self.line_ids:
            line.write({
                'journal_id': self.payment_journal_id.id,
                'payment_date': self.payment_date,
            })

class PRLFeeDriver(models.Model):
    _name = 'prl.fee.driver'
    _description = 'Payment Request Line Fee Driver'
    _inherit = 'payment.request.line'

    @api.depends('fee_id')
    def _count_amount(self):
        for doc in self:
            if doc.fee_id:
                fee = self.env['fee.driver.line'].search([ ('id', '=', doc.fee_id.id) ])
                if fee: doc.update({ 'amount': fee.amount })

    payment_id = fields.Many2one('pr.fee.driver', string='Payment Reference', required=True, ondelete='cascade', index=True, copy=False)
    fee_id = fields.Many2one('fee.driver.line', string='Source Document', required=True, ondelete='cascade', index=True, copy=False, domain=[('state', '=', 'open')])
    amount = fields.Monetary('Amount', compute='_count_amount', readonly=True, store=True)
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            fee = self.env['fee.driver.line'].search([('id', '=', vals['fee_id'])], limit=1)
            vals['name'] = fee.name or '/'
            vals['communication'] = fee.fee_id.name
            
        return super(PRLFeeDriver, self).create(vals)