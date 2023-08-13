from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def action_view_stock_card_product(self):
        self.ensure_one()
        StockCardLine = self.env['stock.card.line']

        products = self.mapped('product_variant_ids')
        StockCardLine.process( products.ids[0] )

        action = self.env.ref('stock_card.stock_card_line_action').read()[0]
        action['domain'] = [('product_id.product_tmpl_id', 'in', self.ids)]
        return action