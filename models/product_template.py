from odoo import api, fields, models, _

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_equipment = fields.Boolean('Equipment', default=False, required=True)