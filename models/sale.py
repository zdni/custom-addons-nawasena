from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)

class SettingProductPricelist(models.Model):
    _name = 'setting.product.pricelist'

    product_id = fields.Many2one('product.template', string='Product', required=True)
    sequence = fields.Integer(help="Used to order the note stages")

    @api.multi
    def unlink(self):
        for rec in self:
            items = self.env['product.pricelist.item'].search([
                ('product_tmpl_id', '=', rec.product_id.id)
            ])
            for item in items:
                item.unlink()

        return super(SettingProductPricelist, self).unlink()
    
    @api.model
    def create(self, vals):
        customers = self.env['res.partner'].search([
            ('customer', '=', True)
        ])
        for customer in customers:
            if customer.property_product_pricelist.is_delivery:
                self.env['product.pricelist.item'].create({
                    'applied_on': '1_product',
                    'product_tmpl_id': vals.get('product_id'),
                    'compute_price': 'fixed',
                    'fixed_price': customer.oat or 0.0,
                    'pricelist_id': customer.property_product_pricelist.id,
                    'is_delivery': True
                })
                
        result = super(SettingProductPricelist, self).create(vals)
        return result
