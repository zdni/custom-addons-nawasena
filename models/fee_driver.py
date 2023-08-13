from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime

import logging
_logger = logging.getLogger(__name__)

class FeeDriver(models.Model):
    _name = 'fee.driver'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = 'Fee Driver'

    def _default_currency_id(self):
        company_id = self.env.context.get('force_company') or self.env.context.get('company_id') or self.env.user.company_id.id
        return self.env['res.company'].browse(company_id).currency_id
    
    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state == 'posted':
                raise UserError(_("Can't Delete Fee Driver Document"))
        return super(FeeDriver, self).unlink()
    
    @api.multi
    def action_draft(self):
        docs = self.filtered(lambda s: s.state in ['cancel'])
        return docs.write({ 'state': 'draft' })

    @api.multi
    def action_cancel(self):
        # check status line_ids
        for line in self.line_ids:
            if not line.state == 'open':
                raise UserError(_("Can't cancel Fee Driver when the line is paid!"))

        # cancel account move
        self.cancel_journal()
    
    @api.multi
    def action_posted(self):
        AccountMove = self.env['account.move']

        # get journal
        journal = self.env.user.company_id.journal_fee_driver_id
        if not journal:
            raise UserError(_("Set Journal for Free Driver!"))

        # create journal for fee driver
        credit_line = {
            'account_id': journal.default_credit_account_id.id,
            'name': journal.default_credit_account_id.name,
            'debit': 0,
            'credit': self.amount_total,
        }
        debit_line = {
            'account_id': journal.default_debit_account_id.id,
            'name': journal.default_debit_account_id.name,
            'debit': self.amount_total,
            'credit': 0,
        }
        move = AccountMove.create({
            'date': fields.Date.today(),
            'journal_id': journal.id,
            'ref': self.name,
            'state': 'posted',
            'name': self.name,
            'company_id': self.env.user.company_id.id,
            'line_ids': [(0, 0, debit_line), (0, 0, credit_line)]
        })

        # update fee driver document
        self.write({ 'journal_id': move.id, 'state': 'posted' })
    
    @api.depends('line_ids.amount')
    def _amount_all(self):
        for doc in self:
            amount_total = 0
            for line in doc.line_ids:
                amount_total += line.amount

            doc.update({ 'amount_total': amount_total })
    
    name = fields.Char('Name', required=True, copy=False, index=True, default=lambda self: _('New'))
    delivery_date = fields.Date('Delivery Date', required=True, default=lambda self: fields.Date.today())
    journal_id = fields.Many2one('account.move', string='Journal Entry', readonly=True)
    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all')
    line_ids = fields.One2many('fee.driver.line', 'fee_id', string='Fee Lines', states={'draft': [('readonly', False)]}, copy=True, readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancel', 'Cancel'),
    ], string='State', required=True, readonly=True, default="draft")

    fee_handover_only = fields.Monetary('Fee Handover Only', default=150000, required=True)
    fee_handover = fields.Monetary('Fee Handover', default=75000, required=True)
    
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, readonly=True, default=lambda self: self.env.user.company_id.id)
    currency_id = fields.Many2one("res.currency", string="Currency", readonly=True, required=True, default=_default_currency_id)

    @api.model
    def create(self, vals):
        fee = self.env['fee.driver'].search([ ('delivery_date', '=', vals['delivery_date']) ])
        if fee: raise UserError(_("Unable to Create Fee Driver Document with the same Delivery Date!"))

        company_id = vals.get('company_id', self.default_get(['company_id'])['company_id'])
        if vals.get('name', 'New') == 'New':
            vals['name'] = 'FDR/NMS/' + str(datetime.strptime(vals['delivery_date'], '%Y-%m-%d').strftime(('%d/%m/%Y')))
            
        return super(FeeDriver, self.with_context(company_id=company_id)).create(vals)
    
    def print_doc(self):
        return self.env.ref('fee_driver.action_report_fee_driver')\
            .with_context(discard_logo_check=True).report_action(self)
    
    def calculate_fee(self):
        lines = self.env['fee.driver.line'].search([
            ('fee_id', '=', self.id)
        ], order='driver_id desc, type asc')
        drivers = []

        for line in lines:
            if line.type == 'delivery':
                # get capacity
                vehicle = line.vehicle_id
                customer = line.order_ids[0].partner_shipping_id.parent_id or line.order_ids[0].partner_shipping_id
                delivery = self.env['solar.usage.delivery'].search([
                    ('capacity_id.id', '=', vehicle.capacity_id.id),
                    ('customer_id.id', '=', customer.id),
                ], limit=1)
                fee = delivery.fee if delivery else 0

                line.write({ 'amount': fee })
                drivers.append(line.driver_id.id)
            
            if line.type == 'handover':
                fee = self.fee_handover if line.driver_id.id in drivers else self.fee_handover_only
                line.write({ 'amount': fee })


    def generate_fee(self):
        for line in self.line_ids:
            line.unlink()

        handovers = self.env['tank.handover'].search([ ('delivery_date', '=', self.delivery_date), ('is_fee', '=', True) ], order='driver_id ASC')
        for handover in handovers:
            vehicle_id = handover.vehicle_id.id if handover.vehicle_id else False
            order_ids = [(4, order.id) for order in handover.order_ids]
            self.env['fee.driver.line'].create({
                'fee_id': self.id,
                'name': handover.driver_id.name,
                'driver_id': handover.driver_id.id,
                'vehicle_id': vehicle_id,
                'type': 'handover',
                'order_ids': order_ids,
                'state': 'open',
                'amount': 0,
                'delivery_date': self.delivery_date,
                'handover_id': handover.id,
            })

        deliveries = self.env['delivery.driver'].search([ ('delivery_date', '=', self.delivery_date) ], order='driver_id ASC')
        for delivery in deliveries:
            vehicle = delivery.vehicle_id
            order_ids = [(4, delivery.order_id.id)]
            if len(delivery.change_vehicle_ids) > 0:
                vehicle = delivery.change_vehicle_ids[len(delivery.change_vehicle_ids)-1].vehicle_id
            
            self.env['fee.driver.line'].create({
                'fee_id': self.id,
                'name': delivery.driver_id.name,
                'driver_id': delivery.driver_id.id,
                'vehicle_id': vehicle.id,
                'type': 'delivery',
                'order_ids': order_ids,
                'state': 'open',
                'amount': 0,
                'delivery_date': self.delivery_date,
                'delivery_id': delivery.id,
            })

    def cancel_journal(self):
        if self.journal_id:
            self.journal_id.button_cancel()
            self.journal_id.unlink()
            
            for line in self.line_ids:
                line.cancel_journal()
            
        self.write({ 'journal_id': False, 'state': 'draft' })
    
class FeeDriverLine(models.Model):
    _name = 'fee.driver.line'
    _order = 'driver_id ASC'

    def _default_currency_id(self):
        company_id = self.env.context.get('force_company') or self.env.context.get('company_id') or self.env.user.company_id.id
        return self.env['res.company'].browse(company_id).currency_id

    fee_id = fields.Many2one('fee.driver', string='Source Document', required=True, ondelete='cascade', index=True, copy=False)
    name = fields.Char('Name', readonly=True, default="Driver")
    driver_id = fields.Many2one('res.partner', string='Driver', required=True, domain=[('is_driver', '=', True)])
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle')
    type = fields.Selection([
        ('handover', 'Tank Handover'),
        ('delivery', 'Delivery'),
    ], string='Type', required=True)
    amount = fields.Monetary('Fee', required=True)
    order_ids = fields.Many2many('sale.order', string='Order Ref')
    journal_id = fields.Many2one('account.move', string='Journal Entry', readonly=True)
    state = fields.Selection([
        ('open', 'Open'),
        ('paid', 'Paid'),
    ], string='State', default='open')
    ref = fields.Char('Source Document')
    delivery_date = fields.Date('Delivery Date')

    delivery_id = fields.Many2one('delivery.driver', string='Doc Reference')
    handover_id = fields.Many2one('tank.handover', string='Doc Reference')

    currency_id = fields.Many2one("res.currency", string="Currency", readonly=True, required=True, default=_default_currency_id)
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, readonly=True, default=lambda self: self.env.user.company_id.id)

    @api.onchange('driver_id')
    def _onchange_driver_id(self):
        if self.driver_id:
            vehicle = self.env['fleet.vehicle'].search([ ('driver_id.id', '=', self.driver_id.id) ], limit=1)
            if vehicle: self.vehicle_id = vehicle.id

    def name_get(self):
        res = []
        for rec in self:
            name = rec.name
            doc_name = rec.fee_id.name
            res.append((rec.id, doc_name + ", " + name))
        
        return res
    
    def cancel_journal(self):
        if self.journal_id:
            self.journal_id.button_cancel()
            self.journal_id.unlink()

        self.write({ 'journal_id': False, 'state': 'open' })

    @api.multi
    def unlink(self):
        for rec in self:
            rec.cancel_journal()

            if rec.fee_id.journal_id: rec.fee_id.cancel_journal()

        return super(FeeDriverLine, self).unlink()