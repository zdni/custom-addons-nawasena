from odoo import api, fields, models, _

class ResCompany(models.Model):
    _inherit = "res.company"

    journal_fee_driver_id = fields.Many2one('account.journal', string="Journal Fee Driver")