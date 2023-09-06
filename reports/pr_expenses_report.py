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
        mode = {
            'own_account': 'Employee (to reimburse)',
            'company_account': 'Company',
        }

        expenses = []
        total_expenses = 0
        for line in docs.line_ids:
            sheet = line.sheet_id
            data = {
                'name': sheet.name,
                'date': sheet.expense_line_ids[0].date.strftime('%d %b %Y') or '',
                'employee': sheet.employee_id.name,
                'payment_by': mode[sheet.payment_mode],
                'notes': sheet.expense_line_ids[0].description or '',
                'amount': sheet.total_amount,
            }
            expenses.append(data)
            
            total_expenses += sheet.total_amount 

        return {
            'doc_model': 'pr.expense',
            'data': data,
            'docs': docs,
            'expenses': expenses,
            'total_expenses': total_expenses
        }