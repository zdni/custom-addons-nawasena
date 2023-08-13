from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    is_delivery = fields.Boolean('Delivery', default=True)
    delivery_number = fields.Char('Delivery Number')
    order_number = fields.Char('Order Number')
    product_delivery_id = fields.Many2one('product.product', string='Product Delivery', domain=[('delivery_ok', '=', True)])
    delivery_date = fields.Date('Delivery Date', default=fields.Date.today(), required=True)

    # driver
    def action_view_driver_delivery(self):
        docs = self.env['delivery.driver'].search([('order_id.id', '=', self.id)])
        action = self.env.ref('custom_delivery.action_delivery_driver').read()[0]
        if len(docs) > 0:
            action['domain'] = [('id', 'in', docs.ids)]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action
    
    def action_view_driver_handover(self):
        docs = self.env['tank.handover'].search([('order_ids', 'in', self.id)])
        action = self.env.ref('custom_delivery.action_tank_handover').read()[0]
        if len(docs) > 0:
            action['domain'] = [('id', 'in', docs.ids)]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    def act_view_driver_wizard(self):
        return {    
            'name': _("Pickup at Depot"),
            'type': 'ir.actions.act_window',
            'res_model': 'delivery.driver.wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'context': { 'default_delivery_date': self.delivery_date }
        }
    
    def calculate_solar_usage(self):
        product = self.env.user.company_id.product_usage_id

        # handover 
        handovers = self.env['tank.handover'].search([
            ('order_ids', 'in', self.id), 
            ('fuel_id', '=', False),
            ('is_fee', '=', True),
        ])
        for handover in handovers:
            if handover.is_fee:
                if handover.vehicle_id:
                    fuel = self.env['fleet.vehicle.log.fuel'].create({
                        'vehicle_id': handover.vehicle_id.id,
                        'liter': 1,
                        'price_per_liter': product.standard_price,
                        'amount': 1*product.standard_price,
                        'odometer': handover.vehicle_id.odometer,
                        'notes': 'Masuk Depot ' + str(handover.name),
                        'date': handover.delivery_date,
                        'purchaser_id': handover.driver_id.id,
                    })
                    handover.write({ 'fuel_id': fuel.id })

        deliveries = self.env['delivery.driver'].search([ 
            ('order_id.id', '=', self.id),
            ('fuel_id', '=', False),
        ])
        for delivery in deliveries:
            customer = self.partner_shipping_id.parent_id
            vehicle = delivery.vehicle_id
            if len(delivery.change_vehicle_ids) > 0:
                vehicle = delivery.change_vehicle_ids[len(delivery.change_vehicle_ids)-1].vehicle_id

            usage = self.env['solar.usage.delivery'].search([
                ('capacity_id.id', '=', vehicle.capacity_id.id),
                ('customer_id.id', '=', customer.id),
            ])
            liter = usage.solar_usage
            odometer = vehicle.odometer + (customer.mileage*2)
            note = 'Pengantaran ke ' + str(customer.name) + " " + str(delivery.order_id.name)
             
            fuel = self.env['fleet.vehicle.log.fuel'].create({
                'vehicle_id': vehicle.id,
                'liter': liter,
                'price_per_liter': product.standard_price,
                'amount': liter*product.standard_price,
                'odometer': odometer,
                'notes': note,
                'date': delivery.delivery_date,
                'purchaser_id': delivery.driver_id.id,
            })
            
            delivery.write({ 'fuel_id': fuel.id })

    @api.multi
    def action_cancel(self):
        for rec in self:
            childs = self.env['delivery.driver'].search([ ('order_id.id', '=', rec.id) ])
            for child in childs:
                child.unlink()
        
            handovers = self.env['tank.handover'].search([ ('order_ids', 'in', rec.id) ])
            for handover in handovers:
                if len(handover.order_ids) == 1: handover.unlink()

        return super(SaleOrder, self).action_cancel()

    @api.onchange('partner_shipping_id')
    def _onchange_partner_shipping_id(self):
        if self.partner_shipping_id:
            self.pricelist_id = self.partner_shipping_id.property_product_pricelist.id