from odoo import api, fields, models, _

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    asset_debt_id = fields.Many2one('account.account', string='Account Asset Debt', related='company_id.account_asset_debt_id', readonly=False)
    bank_debt_id = fields.Many2one('account.account', string='Account Bank Debt', related='company_id.account_bank_debt_id', readonly=False)
    installments_diff_id = fields.Many2one('account.account', string='Account Installments Diff', related='company_id.account_installments_diff_id', readonly=False)
    interest_debt_id = fields.Many2one('account.account', string='Account Interest Debt', related='company_id.account_interest_debt_id', readonly=False)
    leasing_id = fields.Many2one('account.journal', string='Journal Leasing', related='company_id.journal_leasing_id', readonly=False)