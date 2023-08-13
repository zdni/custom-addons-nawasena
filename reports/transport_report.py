from odoo import fields, models, api, _
from datetime import timedelta

import pytz

import logging
_logger = logging.getLogger(__name__)

class TransportReport(models.AbstractModel):
    _name = "report.report_transport.report_transport"
    _description = "Report Transport"

    @api.model
    def get_report(self, start_date=False, end_date=False, customer_ids=False):
        user_currency = self.env.user.company_id.currency_id
        if not customer_ids:
            customer_ids = self.env['res.partner'].search([ ('customer', '=', True) ])
        
        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        today = user_tz.localize(fields.Datetime.from_string(fields.Date.context_today(self)))
        today = today.astimezone(pytz.timezone('UTC'))
        if start_date:
            start_date = fields.Datetime.from_string(start_date)
        else:
            start_date = today

        if end_date:
            end_date = fields.Datetime.from_string(end_date)
        else:
            end_date = today + timedelta(days=1, seconds=-1)
         
        end_date = max(end_date, start_date)

        start_date = fields.Datetime.to_string(start_date)
        end_date = fields.Datetime.to_string(end_date)

        order_arr = []
        datas = {
            'start_date': start_date,
            'end_date': end_date,
            'customer': {}
        }

        for customer in customer_ids:
            # orders
            orders = self.env['sale.order'].search([
                ('partner_id.id', '=', customer.id),
                ('state', '=', 'sale'),
                ('delivery_date', '>=', start_date),
                ('delivery_date', '<=', end_date),
            ])
            for order in orders:
                already = False
                partner = order.partner_shipping_id
                
                # deliveries
                deliveries = self.env['delivery.driver'].search([
                    ('order_id.id', '=', order.id),
                    ('type', '=', 'delivery'),
                ])
                for delivery in deliveries:
                    if (order.id, delivery.driver_id.id) in order_arr:
                        continue

                    order_arr.append((order.id, delivery.driver_id.id))
                    vehicle = delivery.vehicle_id
                    if len(delivery.change_vehicle_ids) > 0:
                        vehicle = delivery.change_vehicle_ids[len(delivery.change_vehicle_ids)-1].vehicle_id

                    dlv = self.env['solar.usage.delivery'].search([
                        ('capacity_id.id', '=', vehicle.capacity_id.id),
                        ('customer_id.id', '=', partner.parent_id.id),
                    ], limit=1)
                    fee = dlv.fee or 0

                    data = {
                        'date': delivery.delivery_date,
                        'order_number': order.order_number,
                        'delivery_number': order.delivery_number,
                        'travel': 'SJ/NMS/' + str(delivery.name[10:]),
                        'driver': delivery.driver_id.name,
                        'plate': vehicle.license_plate,
                        'destination': partner.parent_id.name,
                        'location': partner.city,
                        'qty': vehicle.capacity_id.name,
                        'oat': partner.parent_id.oat,
                        'total': order.amount_total,
                        'solar_usage': delivery.fuel_id.amount or 0,
                        'fee': fee or 0,
                        'income': order.amount_total - fee
                    }

                    if customer.name in datas['customer']:
                        datas['customer'][customer.name]['lines'].append(data)
                        datas['customer'][customer.name]['total_qty'] += data['qty']
                        datas['customer'][customer.name]['total'] += data['total']
                        datas['customer'][customer.name]['total_solar_usage'] += data['solar_usage']
                        datas['customer'][customer.name]['total_fee'] += data['fee']
                        datas['customer'][customer.name]['total_income'] += data['income']
                    else:
                        datas['customer'][customer.name] = {
                            'total_qty': data['qty'],
                            'total': data['total'],
                            'total_solar_usage': data['solar_usage'],
                            'total_fee': data['fee'],
                            'total_income': data['income'],
                            'lines': [data]
                        }


                # handover + delivery
                deliveries = self.env['delivery.driver'].search([
                    ('order_id.id', '=', order.id),
                    ('type', '=', 'handover'),
                    ('is_delivery', '=', True),
                ])
                for delivery in deliveries:
                    if (order.id, delivery.driver_id.id) in order_arr:
                        continue
                    
                    order_arr.append((order.id, delivery.driver_id.id))
                    vehicle = delivery.vehicle_id
                    if len(delivery.change_vehicle_ids) > 0:
                        vehicle = delivery.change_vehicle_ids[len(delivery.change_vehicle_ids)-1].vehicle_id

                    dlv = self.env['solar.usage.delivery'].search([
                        ('capacity_id.id', '=', vehicle.capacity_id.id),
                        ('customer_id.id', '=', partner.parent_id.id),
                    ], limit=1)
                    fee = dlv.fee or 0

                    data = {
                        'date': delivery.delivery_date,
                        'order_number': order.order_number,
                        'delivery_number': order.delivery_number,
                        'travel': 'SJ/NMS/' + str(delivery.name[10:]),
                        'driver': delivery.driver_id.name,
                        'plate': vehicle.license_plate,
                        'destination': partner.parent_id.name,
                        'location': partner.city,
                        'qty': vehicle.capacity_id.name,
                        'oat': partner.parent_id.oat,
                        'total': order.amount_total,
                        'solar_usage': delivery.fuel_id.amount or 0,
                        'fee': fee or 0,
                        'income': order.amount_total - fee
                    }

                    if customer.name in datas['customer']:
                        datas['customer'][customer.name]['lines'].append(data)
                        datas['customer'][customer.name]['total_qty'] += data['qty']
                        datas['customer'][customer.name]['total'] += data['total']
                        datas['customer'][customer.name]['total_solar_usage'] += data['solar_usage']
                        datas['customer'][customer.name]['total_fee'] += data['fee']
                        datas['customer'][customer.name]['total_income'] += data['income']
                    else:
                        datas['customer'][customer.name] = {
                            'total_qty': data['qty'],
                            'total': data['total'],
                            'total_solar_usage': data['solar_usage'],
                            'total_fee': data['fee'],
                            'total_income': data['income'],
                            'lines': [data]
                        }

                if not already:
                    qty = order.order_line[0].product_uom_qty
                    data = {
                        'date': order.delivery_date,
                        'order_number': order.order_number,
                        'delivery_number': order.delivery_number,
                        'travel': '-',
                        'driver': '-',
                        'plate': '-',
                        'destination': partner.parent_id.name,
                        'location': partner.city,
                        'qty': qty,
                        'oat': partner.parent_id.oat,
                        'total': order.amount_total,
                        'solar_usage': 0,
                        'fee': 0,
                        'income': order.amount_total
                    }
                    if customer.name in datas['customer']:
                        datas['customer'][customer.name]['lines'].append(data)
                        datas['customer'][customer.name]['total_qty'] += data['qty']
                        datas['customer'][customer.name]['total'] += data['total']
                        datas['customer'][customer.name]['total_solar_usage'] += data['solar_usage']
                        datas['customer'][customer.name]['total_fee'] += data['fee']
                        datas['customer'][customer.name]['total_income'] += data['income']
                    else:
                        datas['customer'][customer.name] = {
                            'total_qty': data['qty'],
                            'total': data['total'],
                            'total_solar_usage': data['solar_usage'],
                            'total_fee': data['fee'],
                            'total_income': data['income'],
                            'lines': [data]
                        }

        return {
            'currency_precision': user_currency.decimal_places,
            'datas': datas
        }

    @api.multi
    def _get_report_values(self, docids, data=None):
        data = dict(data or {})
        customer_ids = self.env['res.partner'].browse(data['customer_ids'])
        data.update(self.get_report(data['start_date'], data['end_date'], customer_ids))
        return data