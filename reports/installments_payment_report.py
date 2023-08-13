from odoo import api, models, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

class InstallmentsPaymentReport(models.AbstractModel):
    _name = "report.installments_payment.report_installments_payment"
    _description = "Installments Payment Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['installments.payment'].browse(docids[0])

        return {
            'doc_model': 'installments.payment',
            'data': data,
            'docs': docs,
            'state': {
                'open': 'Belum Terbayar',
                'paid': 'Terbayar',
            },
            'state_doc': {
                'draft': 'Draft',
                'approved': 'Disetujui',
                'done': 'Selesai',
                'cancel': 'Batal',
            },
            'interest_type': {
                'annuity': 'Anuitas',
                'flat': 'Bunga Flat',
                'decreased': 'Bunga Menurun',
            },
            'type': {
                'bank': 'Bank',
                'leasing': 'Leasing',
            }
        }