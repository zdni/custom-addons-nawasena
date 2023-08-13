from odoo import api, fields, models, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

class StockInventory(models.Model):
    _inherit = 'stock.inventory'

    reverse_doc_id = fields.Many2one('stock.inventory', string='Reverse Doc Reference')