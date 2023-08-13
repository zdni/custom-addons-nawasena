from odoo import api, models, _

class FeeDriverReport(models.AbstractModel):
    _name = "report.fee_driver.report_fee_driver"
    _description = "Fee Driver Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['fee.driver'].browse(docids[0])

        return {
            'doc_model': 'fee.driver',
            'data': data,
            'docs': docs,
            'state' : {
                'doc': {
                    'draft': 'Draft',
                    'posted': 'Posted',
                    'cancel': 'Cancel'
                },
                'line': {
                    'open': 'Belum Dibayar',
                    'paid': 'Terbayar'
                },
            },
            'type': {
                'handover': 'Oper Tangki',
                'delivery': 'Pengantaran'
            },
        }