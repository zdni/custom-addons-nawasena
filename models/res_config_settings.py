from odoo import api, fields, models, _

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    product_usage_id = fields.Many2one('product.product', string='Product Usage', related='company_id.product_usage_id', readonly=False)
    handover_location = fields.Char('Handover Location', related='company_id.handover_location', readonly=False)

    handover_state_id = fields.Many2one('fleet.vehicle.state', string='Handover State', related='company_id.handover_state_id', readonly=False)
    delivery_state_id = fields.Many2one('fleet.vehicle.state', string='Delivery State', related='company_id.delivery_state_id', readonly=False)
    maintenance_state_id = fields.Many2one('fleet.vehicle.state', string='Maintenance State', related='company_id.maintenance_state_id', readonly=False)
    logo_icon = fields.Binary('Logo Icon', related='company_id.logo_icon', readonly=False)
    signature = fields.Binary('Signature', related='company_id.signature', readonly=False)