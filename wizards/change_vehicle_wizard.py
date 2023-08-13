from odoo import api, fields, models, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

class ChangeVehicleWizard(models.TransientModel):
    _name = 'change.vehicle.wizard'

    driver_id = fields.Many2one('res.partner', string='Driver', domain=[('is_driver', '=', True)], required=True)
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle')

    @api.multi
    def create_docs(self):
        docs = self.env['delivery.driver'].browse(self._context.get('active_ids', []))
        for doc in docs:
            self.env['driver.change.vehicle'].create({ 
                'delivery_id':  doc.id,
                'driver_id': self.driver_id.id,
                'vehicle_id': self.vehicle_id.id,
            })

        if self._context.get('open_docs', False):
            return docs.action_view_change_vehicle()
        return {'type': 'ir.actions.act_window_close'}
    
    @api.onchange('driver_id')
    def _onchange_driver_id(self):
        if self.driver_id:
            vehicle = self.env['fleet.vehicle'].search([('driver_id.id', '=', self.driver_id.id)], limit=1)
            if vehicle: self.vehicle_id = vehicle.id
