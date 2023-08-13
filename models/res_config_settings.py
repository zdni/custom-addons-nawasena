from odoo import api, fields, models, _

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    fee_driver_id = fields.Many2one('account.journal', string='Journal Fee Driver', related='company_id.journal_fee_driver_id', readonly=False)