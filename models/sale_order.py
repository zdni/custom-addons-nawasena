from odoo import api, fields, models, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def action_cancel(self):
        fees = self.env['fee.driver.line'].search([ ('order_ids', 'in', self.id) ])
        for fee in fees:
            fee.unlink()

        return super(SaleOrder, self).action_cancel()