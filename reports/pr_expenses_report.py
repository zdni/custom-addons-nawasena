from odoo import api, models, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

class PRExpensesReport(models.AbstractModel):
    _name = "report.pr_expenses.report_pr_expenses"
    _description = "Payment Request Expenses Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['pr.expense'].browse(docids[0])

        return {
            'doc_model': 'pr.expense',
            'data': data,
            'docs': docs,
        }