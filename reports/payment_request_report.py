from odoo import api, models, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

class PRAccountInvoiceReport(models.AbstractModel):
    _name = "report.pr_invoice.report_pr_account_invoice"
    _description = "Payment Request Vendor Bills"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['pr.account.invoice'].browse(docids[0])

        return {
            'doc_model': 'pr.account.invoice',
            'data': data,
            'docs': docs,
            'state': {
                'open': 'Belum Dibayar',
                'paid': 'Terbayar',
            }
        }