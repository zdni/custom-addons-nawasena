from odoo import api, fields, models, _

class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_driver = fields.Boolean('Driver')