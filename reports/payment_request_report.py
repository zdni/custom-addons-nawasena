from odoo import api, models, _

class PRFeeDriverReport(models.AbstractModel):
    _name = "report.fee_driver.report_pr_fee_driver"
    _description = "Payment Request Fee Driver Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        user_currency = self.env.user.company_id.currency_id
        docs = self.env['pr.fee.driver'].browse(docids[0])
        
        state = {
            'open': 'Belum Dibayar',
            'paid': 'Terbayar',
        }
        results = {}
        for line in docs.line_ids:
            destination = ''
            order = False
            if line.fee_id.type == 'handover':
                destination = 'Oper Tangki'
            else:
                order = line.fee_id.order_ids[0] if line.fee_id.order_ids else False
                if order:
                    partner = order.partner_shipping_id
                    destination = str(partner.parent_id.name or '-') + ', ' +  str(partner.name or '-')

            data = {
                'date': line.fee_id.fee_id.delivery_date,
                'order': order.name if order else '-',
                'origin': 'KENDARI',
                'vehicle': line.fee_id.vehicle_id.license_plate,
                'destination': destination,
                'qty': line.fee_id.vehicle_id.capacity_id.name,
                'fee': line.fee_id.amount,
            }

            if line.fee_id.driver_id.name in results:
                results[line.fee_id.driver_id.name].append(data)
            else:
                results[line.fee_id.driver_id.name] = [data]

        return {
            'currency_precision': user_currency.decimal_places,
            'doc_model': 'pr.fee.driver',
            'data': data,
            'docs': docs,
            'results': results
        }