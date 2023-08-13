from odoo import api, models, _

class TankHandoverReport(models.AbstractModel):
    _name = "report.custom_delivery.report_tank_handover"
    _description = "Tank Handover Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['delivery.driver'].browse(docids[0])

        days = {
            'Sunday': 'Minggu',
            'Monday': 'Senin',
            'Tuesday': 'Selasa',
            'Wednesday': 'Rabu',
            'Thursday': 'Kamis',
            'Friday': 'Jumat',
            'Saturday': 'Sabtu',
        }

        # consignors
        consignors = []
        consignors_name = []
        for handover in docs.doc_ids:
            consignors.append({
                'name': handover.driver_id.name,
                'company_name': handover.driver_id.company_id.name,
                'company_address': handover.driver_id.company_id.street,
                'fleet': handover.vehicle_id.license_plate
            })
            consignors_name.append(handover.driver_id.name)

        # consignee_driver
        consignee_driver = {
            'name': docs.driver_id.name,
            'company_name': docs.driver_id.company_id.name,
            'company_address': docs.driver_id.company_id.street,
            'fleet': docs.vehicle_id.license_plate
        }
        consignors_sign = ', '.join(consignors_name)

        # get qty delivery
        qty = 0
        for line in docs.order_id.order_line:
            # product delivery
            is_prod_del = self.env['setting.product.pricelist'].search([ ('product_id', '=', line.product_id.product_tmpl_id.id) ])
            if is_prod_del:
                qty += line.product_uom_qty

        return {
            'doc_model': 'delivery.driver',
            'data': data,
            'consignors': consignors,
            'consignors_sign': consignors_sign,
            'consignee_driver': consignee_driver,
            'consignors_len': len(consignors),
            'product': {
                'name': docs.order_id.product_delivery_id.name,
                'qty': str(int(qty)) + ' (L)',
            },
            'date': docs.order_id.delivery_date,
            'day': days[docs.order_id.delivery_date.strftime('%A')],
            'location': docs.location,
        }