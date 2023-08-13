from odoo import api, fields, models, _
from datetime import date
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

class TankHandoverWizard(models.TransientModel):
    _name = 'tank.handover.wizard'

    location = fields.Char('Location', required=True)

    order_id = fields.Many2one('sale.order', string='Order', required=True, domain=[('state', '=', 'sale')])
    consignee_driver_id = fields.Many2one('res.partner', string='Consignee Driver', required=True, domain=[('is_driver', '=', True)])
    consignor_driver_id = fields.Many2one('res.partner', string='Consignor Driver', required=True, domain=[('is_driver', '=', True)], readonly=True)
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle')

    @api.onchange('consignee_driver_id')
    def _onchange_consignee_driver_id(self):
        if self.consignee_driver_id:
            vehicle = self.env['fleet.vehicle'].search([('driver_id.id', '=', self.consignee_driver_id.id)], limit=1)
            if vehicle: self.vehicle_id = vehicle.id
        
    @api.multi
    def create_docs(self):
        docs = self.env['tank.handover'].browse(self._context.get('active_ids', []))
        DeliveryDriver = self.env['delivery.driver']

        if not self.vehicle_id: raise UserError(_("Set Vehicle!"))

        for doc in docs:
            DeliveryDriver.create({
                'order_id': self.order_id.id,
                'driver_id': self.consignee_driver_id.id, 
                'vehicle_id': self.vehicle_id.id,
                'delivery_date': doc.delivery_date,
                'end_date': doc.delivery_date,
                'doc_ids': [(4, doc.id)], #?
                'location': self.location,
            })

        return {'type': 'ir.actions.act_window_close'}