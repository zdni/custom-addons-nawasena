from odoo import api, models, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

class HandoverDeliveryReport(models.AbstractModel):
    _name = "report.custom_delivery.report_handover_delivery"
    _description = "Handover Delivery Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        user_currency = self.env.user.company_id.currency_id
        docs = self.env['delivery.driver'].browse(docids[0])

        # get conditions
        handover_conditions = self.env['handover.conditions'].search([])
        conditions = [condition.name for condition in handover_conditions]
        
        # get qty delivery
        qty = 0
        for line in docs.order_id.order_line:
            # product delivery
            is_prod_del = self.env['setting.product.pricelist'].search([ ('product_id', '=', line.product_id.product_tmpl_id.id) ])
            if is_prod_del:
                qty += line.product_uom_qty

        # get driver
        driver = docs.driver_id

        # get vehicle
        vehicle = docs.vehicle_id
        if len(docs.change_vehicle_ids) > 0:
            vehicle = docs.change_vehicle_ids[len(docs.change_vehicle_ids)-1].vehicle_id
        
        # get gauge tank
        gauge_tank_log = self.env['fleet.gauge.tank.log'].search([
            ('vehicle_id', '=', vehicle.id)
        ], limit=1, order='id desc')
        
        return {
            'doc_model': 'delivery.driver',
            'currency_precision': user_currency.decimal_places,
            'data': data,
            'product': {
                'name': docs.order_id.product_delivery_id.name,
                'qty': str(int(qty)) + " L",
            },
            'driver': {
                'name': driver.name
            },
            'vehicle': {
                'license_plate': vehicle.license_plate,
                'tank_capacity': str(int(vehicle.capacity_id.name)) + " L",
                'gauge_tank': str(gauge_tank_log.value).replace('.', ',') or '0'
            },
            'conditions': conditions,
            'company_': {
                'name': driver.company_id.name,
                'director_name': 'DEDY KURNIAWAN'
            },
            'customer': {
                'name': docs.order_id.partner_shipping_id.parent_id.name
            },
            'date': docs.order_id.delivery_date,
        }