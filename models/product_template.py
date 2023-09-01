from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def action_view_stock_card_product(self):
        self.generate_stock_card()

        action = self.env.ref('stock_card.stock_card_line_action').read()[0]
        action['domain'] = [('product_id.product_tmpl_id', 'in', self.ids)]
        return action
    
    @api.multi
    def refresh_stock_card(self):
        products = self.mapped('product_variant_ids')
        product_id = products.ids[0]

        lines = self.env['stock.card.line'].search([ ('product_id', '=', product_id) ])
        for line in lines: line.unlink()

        moves = self.env['stock.move'].search([
            ('product_id.id', '=', product_id),
            ('has_count', '=', True),
            ('state', '=', 'done'),
        ])
        for move in moves: move.write({ 'has_count': False })

    def generate_stock_card(self):
        StockCardLine = self.env['stock.card.line']

        products = self.mapped('product_variant_ids')
        StockCardLine.process( products.ids[0] )