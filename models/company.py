from odoo import api, fields, models, _

class ResCompany(models.Model):
    _inherit = "res.company"

    account_asset_debt_id = fields.Many2one('account.account', string="Account Asset Debt")
    account_bank_debt_id = fields.Many2one('account.account', string="Account Bank Debt")
    account_installments_diff_id = fields.Many2one('account.account', string="Account Installments Diff")
    account_interest_debt_id = fields.Many2one('account.account', string="Account Interest Debt")
    journal_leasing_id = fields.Many2one('account.journal', string="Journal Leasing")