from odoo import api, models, _
from odoo.exceptions import UserError
from num2words import num2words
import roman

class TravelDocReport(models.AbstractModel):
    _name = "report.custom_delivery.report_travel_doc"
    _description = "Travel Document Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['delivery.driver'].browse(docids[0])
        company = docs.driver_id.company_id

        # get qty delivery
        qty = 0
        qty_str = ''
        for line in docs.order_id.order_line:
            # product delivery
            is_prod_del = self.env['setting.product.pricelist'].search([ ('product_id', '=', line.product_id.product_tmpl_id.id) ])
            if is_prod_del:
                qty += line.product_uom_qty
        qty_str = num2words(int(qty), lang="id")

        # get driver
        driver = docs.driver_id

        # vehicle
        vehicle = docs.vehicle_id
        if len(docs.change_vehicle_ids) > 0:
            vehicle = docs.change_vehicle_ids[len(docs.change_vehicle_ids)-1].vehicle_id
        # get gauge tank
        gauge_tank_log = self.env['fleet.gauge.tank.log'].search([
            ('vehicle_id.id', '=', vehicle.id),
        ])
        gauge_tank = []
        for line in gauge_tank_log:
            gauge_tank.append(str(line.value))
        # seal number
        seal_number_ids = docs.seal_number_ids
        if len(docs.change_vehicle_ids) > 0:
            seal_number_ids = docs.change_vehicle_ids[len(docs.change_vehicle_ids)-1].seal_number_ids

        top_seal = []
        bottom_seal = []
        for line in seal_number_ids:
            if line.position == 'top':
                for seal in line.seal_ids:
                    top_seal.append(seal.name)
            if line.position == 'bottom':
                for seal in line.seal_ids:
                    bottom_seal.append(seal.name)

        top_seal = sorted(top_seal) 
        bottom_seal = sorted(bottom_seal) 

        # top_seal = [line.seal_id.name for line in seal_number_ids.filtered(lambda l: l.position == 'top')]
        # bottom_seal = [line.seal_id.name for line in seal_number_ids.filtered(lambda l: l.position == 'bottom')]

        # generate number travel doc
        number = 'SJ/NMS/' + roman.toRoman(docs.delivery_date.month) + '/' + docs.name[-4:]

        return {
            'doc_model': 'delivery.driver',
            'data': data,
            'docs': docs,
            'doc_': {
                'company': {
                    'name': company.name,
                    'address': company.street,
                    'tax': company.vat,
                    'director_name': 'DEDY KURNIAWAN',
                },
                'number': number,
                'do_number': docs.order_id.delivery_number,
                'so_number': docs.order_id.order_number,
                'date': docs.delivery_date,
                'end_date': docs.end_date,
                'product': {
                    'name': docs.order_id.product_delivery_id.name,
                    'qty': str(int(qty)) + " L",
                    'countable_qty': qty_str.upper() + ' LITER',
                },
                'publisher': docs.order_id.user_id.name,
            },
            'customer': {
                'name': docs.order_id.partner_shipping_id.parent_id.name,
                'address': docs.order_id.partner_shipping_id.street,
                'reference': docs.order_id.client_order_ref,
                'tax': docs.order_id.partner_shipping_id.parent_id.vat,
            },
            'driver': driver.name,
            'vehicle': {
                'type': vehicle.model_id.name,
                'license_plate': vehicle.license_plate,
                'gauge_tank': '%s' % ('/ '.join(gauge_tank)) or '0',
                'top_seal': '%s' % (', '.join(top_seal)),
                'bottom_seal': '%s' % (', '.join(bottom_seal)),
            }
        }