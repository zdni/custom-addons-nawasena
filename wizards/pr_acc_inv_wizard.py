from odoo import api, fields, models, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

class PRAccountInvoiceWizard(models.TransientModel):
    _name = 'pr.acc_inv.wizard'

    doc_id = fields.Integer(string='Doc ID', required=True)
    type = fields.Selection([
        ('recap', 'Rekap'),
        ('detail', 'Detail')
    ], string='Type', required=True, default='recap')

    @api.multi
    def generate_excel(self):
        if (not self.env.user.company_id.logo):
            raise UserError(_("You have to set a logo or a layout for your company."))
        elif (not self.env.user.company_id.external_report_layout_id):
            raise UserError(_("You have to set your reports's header and footer layout."))
        
        data = {'doc_id': self.doc_id, 'type': self.type, 'company_id': self.env.user.company_id.id}
        return self.env.ref('pr_invoice.action_report_pr_account_invoice_xlsx').report_action(self, data=data)
