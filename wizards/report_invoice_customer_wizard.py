import logging

from odoo import fields, models, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class ReportInvoiceCustomerWizard(models.TransientModel):
    _name = 'report.invoice.customer.wizard'

    start_date = fields.Date('Start Date', required=True)
    end_date = fields.Date('End Date', required=True)
    customer_ids = fields.Many2many('res.partner', string='Customer', domain=[('customer', '=', True)])

    @api.onchange('start_date')
    def _onchange_start_date(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            self.end_date = self.start_date

    @api.onchange('end_date')
    def _onchange_end_date(self):
        if self.end_date and self.end_date < self.start_date:
            self.start_date = self.end_date

    @api.multi
    def generate_report(self):
        if (not self.env.user.company_id.logo):
            raise UserError(_("You have to set a logo or a layout for your company."))
        elif (not self.env.user.company_id.external_report_layout_id):
            raise UserError(_("You have to set your reports's header and footer layout."))
        
        data = {'start_date': self.start_date, 'end_date': self.end_date, 'customer_ids': self.customer_ids.ids}
        return self.env.ref('report_invoice.action_report_invoice_customer').with_context().report_action([], data=data)
        
    @api.multi
    def generate_excel(self):
        if (not self.env.user.company_id.logo):
            raise UserError(_("You have to set a logo or a layout for your company."))
        elif (not self.env.user.company_id.external_report_layout_id):
            raise UserError(_("You have to set your reports's header and footer layout."))
        
        data = {'start_date': self.start_date, 'end_date': self.end_date, 'customer_ids': self.customer_ids.ids, 'company_id': self.env.user.company_id.id}
        return self.env.ref('report_invoice.action_report_invoice_customer_xlsx').report_action(self, data=data)