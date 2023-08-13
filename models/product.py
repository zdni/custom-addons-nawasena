from odoo import api, fields, models, _

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    delivery_ok = fields.Boolean('Can be Delivery', default=False)
