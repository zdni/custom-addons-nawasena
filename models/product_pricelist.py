from odoo import api, fields, models, _

class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    is_delivery = fields.Boolean('Delivery Pricelist', required=True, default=False)