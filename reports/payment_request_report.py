from odoo import api, models, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

class PRInstallmentsPaymentReport(models.AbstractModel):
    _name = "report.installments_payment.report_pr_installments_payment"
    _description = "Payment Request Installments Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['pr.installments.payment'].browse(docids[0])

        return {
            'doc_model': 'pr.installments.payment',
            'data': data,
            'docs': docs,
            'state': {
                'open': 'Belum Dibayar',
                'paid': 'Terbayar',
            }
        }