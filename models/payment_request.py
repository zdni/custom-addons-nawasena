from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError

import logging
_logger = logging.getLogger(__name__)

class PRAccountInvoice(models.Model):
    _name = 'pr.account.invoice'
    _inherit = ['payment.request', 'portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = 'Payment Request Bills'

    line_ids = fields.One2many('prl.account.invoice', 'payment_id', string='Bill Lines', states={'draft': [('readonly', False)]}, copy=True, readonly=True)

    start_date = fields.Date('Start Date', default=lambda self: fields.Date.today())
    end_date = fields.Date('End Date', default=lambda self: fields.Date.today())

    @api.multi
    def generate(self):
        for doc in self:
            if not doc.start_date or not doc.end_date:
                raise UserError(_("Set Start Date and End Date!"))

            for line in doc.line_ids: line.unlink()

            bills = self.env['account.invoice'].search([
                ('date_invoice', '>=', doc.start_date),
                ('date_invoice', '<=', doc.end_date),
                ('state', '=', 'open'),
                ('type', '=', 'in_invoice'),
            ])
            for bill in bills:
                self.env['prl.account.invoice'].create({
                    'payment_id': doc.id,
                    'bill_id': bill.id,
                    'amount': bill.residual,
                    'payment_amount': bill.residual,
                })
                
    @api.multi
    def action_done(self):
        for doc in self:
            payment_method = self.env.ref('account.account_payment_method_manual_out')
            for line in doc.line_ids:
                if not line.journal_id:
                    raise UserError(_("Set Account Journal first!"))
                if not line.payment_date:
                    raise UserError(_("Set Payment Date first!"))
                
                # create account payment
                payment = self.env['account.payment'].create({
                    'payment_type': 'outbound',
                    'partner_type': 'supplier',
                    'invoice_ids': [(4, line.bill_id.id)],
                    'partner_id': line.bill_id.partner_id.id,
                    'state': 'draft',
                    'name': line.communication,
                    'amount': line.payment_amount,
                    'journal_id': line.journal_id.id,
                    'payment_date': line.payment_date,
                    'communication': line.communication,
                    'hide_payment_method': True,
                    'payment_method_id': payment_method.id,
                    'payment_method_code': 'manual',
                })
                payment.action_validate_invoice_payment()
                line.write({ 'move_id': payment.id, 'state': 'paid' })
                
            doc.write({ 'state': 'done' })

    @api.multi
    def print_doc(self):
        return self.env.ref('pr_invoice.action_report_pr_account_invoice')\
            .with_context(discard_logo_check=True).report_action(self)

    def apply_for_all_line(self):
        for line in self.line_ids:
            line.write({
                'journal_id': self.payment_journal_id.id,
                'payment_date': self.payment_date,
            })
    
class PRLAccountInvoice(models.Model):
    _name = 'prl.account.invoice'
    _description = 'Payment Request Line Bills'
    _inherit = 'payment.request.line'

    @api.depends('bill_id')
    def _count_amount(self):
        for doc in self:
            if doc.bill_id:
                bill = self.env['account.invoice'].search([ ('id', '=', doc.bill_id.id) ])
                if bill: doc.update({ 'amount': bill.residual })

    payment_id = fields.Many2one('pr.account.invoice', string='Payment Reference', required=True, ondelete='cascade', index=True, copy=False)
    bill_id = fields.Many2one('account.invoice', string='Source Document', required=True, ondelete='cascade', index=True, copy=False, domain=[('state', '=', 'open'), ('type', '=', 'in_invoice')])
    amount = fields.Monetary('Amount Due', compute='_count_amount', readonly=True, store=True)
    payment_amount = fields.Monetary('Payment Amount', required=True)
    move_id = fields.Many2one('account.payment', string='Payment')

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            bill = self.env['account.invoice'].search([ ('id', '=', vals['bill_id']) ], limit=1)
            vals['name'] = bill.number or '/'
            vals['communication'] = bill.number
            
        return super(PRLAccountInvoice, self).create(vals)
