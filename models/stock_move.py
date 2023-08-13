from odoo import api, fields, models, _

class StockMove(models.Model):
    _inherit = 'stock.move'

    has_count = fields.Boolean('Has Count', readonly=True, default=False)