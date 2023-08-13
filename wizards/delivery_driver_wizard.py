from odoo import api, fields, models, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

class DeliveryDriverWizard(models.TransientModel):
    _name = 'delivery.driver.wizard'

    list_ids = fields.One2many('driver.list.wizard', 'doc_id', string='List')
    delivery_date = fields.Date('Delivery Date', required=True, readonly=True)

    @api.multi
    def create_docs(self):
        orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
        can_open = True
        for order in orders:
            for line in self.list_ids:
                if line.is_delivery:
                    location = self.env.user.company_id.handover_location
                    can_open = False
                    self.env['delivery.driver'].create({ 
                        'order_id':  order.id,
                        'driver_id': line.driver_id.id,
                        'vehicle_id': line.vehicle_id.id,
                        'delivery_date': self.delivery_date,
                        'location': location,
                    })
                else:
                    self.env['tank.handover'].create({ 
                        'order_ids':  [(4, order.id)],
                        'driver_id': line.driver_id.id,
                        'vehicle_id': line.vehicle_id.id if line.vehicle_id else False,
                        'delivery_date': self.delivery_date,
                        'is_fee': line.is_fee,
                    })

        if self._context.get('open_docs', False) and can_open:
            return orders.action_view_driver_handover()
        return {'type': 'ir.actions.act_window_close'}
    
class DriverListWizard(models.TransientModel):
    _name = 'driver.list.wizard'

    doc_id = fields.Many2one('pickup.depot.wizard', string='Doc')
    driver_id = fields.Many2one('res.partner', string='Driver', domain=[('is_driver', '=', True)], required=True)
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle')
    is_fee = fields.Boolean('Fee', default=True)
    is_delivery = fields.Boolean('Delivery', default=False)

    @api.onchange('driver_id')
    def _onchange_driver_id(self):
        if self.driver_id:
            vehicle = self.env['fleet.vehicle'].search([('driver_id.id', '=', self.driver_id.id)], limit=1)
            if vehicle: self.vehicle_id = vehicle.id
