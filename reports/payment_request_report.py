from odoo import api, models, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

class PaymentRequestReport(models.AbstractModel):
    _name = "report.payment_request.report_payment_request"
    _description = "Payment Request Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['payment.request'].browse(docids[0])

        return {
            'doc_model': 'payment.request',
            'data': data,
            'docs': docs,
        }