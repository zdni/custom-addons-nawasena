from odoo import api, fields, models, _

class ResCompany(models.Model):
    _inherit = "res.company"

    product_usage_id = fields.Many2one('product.product', string="Product Usage")
    handover_location = fields.Char('Handover Location')

    handover_state_id = fields.Many2one('fleet.vehicle.state', string="Handover State")
    delivery_state_id = fields.Many2one('fleet.vehicle.state', string="Delivery State")
    maintenance_state_id = fields.Many2one('fleet.vehicle.state', string="Maintenance State")

    logo_icon = fields.Binary('Logo Icon')
    signature = fields.Binary('Signature')
