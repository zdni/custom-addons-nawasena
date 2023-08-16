from odoo.http import request
from odoo import fields, models, api, _
from datetime import timedelta

import pytz

import logging
_logger = logging.getLogger(__name__)

class ProjectReportXls(models.AbstractModel):
    _name = 'report.report_transport.report_transport_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        
        start_date = data['start_date']
        end_date = data['end_date']
        customer_ids = data['customer_ids']

        datas = self.generate_report(start_date, end_date, customer_ids)

        user_obj = self.env['res.users'].search([('id', '=', data['context']['uid'])])
        
        sheet = workbook.add_worksheet("Report Transport")

        format1 = workbook.add_format({'font_size': 22, 'bold': True})
        format1.set_align('center')
        format2 = workbook.add_format({'font_size': 11, 'bold': True, 'bg_color': '#D3D3D3'})
        format2.set_border()
        format3 = workbook.add_format({'font_size': 10})
        format4 = workbook.add_format({'font_size': 14})
        format5 = workbook.add_format({'font_size': 10})
        format5.set_border()
        format6 = workbook.add_format({'font_size': 10, 'num_format': 'd mmm yyyy'})
        format6.set_border()
        format7 = workbook.add_format({'font_size': 10, 'num_format': 'd mmm yyyy'})
        format8 = workbook.add_format({'font_size': 10})
        format8.set_align('center')
        
        # company
        sheet.write('A1', user_obj.company_id.name, format3)
        sheet.write('A2', user_obj.company_id.street, format3)
        sheet.write('A3', user_obj.company_id.city, format3)
        sheet.write('B3', user_obj.company_id.zip, format3)
        sheet.write('A4', user_obj.company_id.state_id.name, format3)
        sheet.write('A5', user_obj.company_id.country_id.name, format3)
        
        sheet.merge_range(6, 0, 7, 14, "LAPORAN ANGKUTAN", format1)
        
        sheet.write('G10', fields.Datetime.from_string(start_date), format7)
        sheet.write('H10', 'sampai', format8)
        sheet.write('I10', fields.Datetime.from_string(end_date), format7)
        

        row_number = 10
        for customer in datas.keys():
            row_number += 2
            sheet.merge_range(row_number, 0, row_number, 14, customer, format4)
            row_number += 2

            sheet.write('A'+str(row_number), "Tanggal", format2)
            sheet.write('B'+str(row_number), "SO", format2)
            sheet.write('C'+str(row_number), "DO", format2)
            sheet.write('D'+str(row_number), "SJ", format2)
            sheet.write('E'+str(row_number), "Driver", format2)
            sheet.write('F'+str(row_number), "Plat", format2)
            sheet.write('G'+str(row_number), "Tujuan", format2)
            sheet.write('H'+str(row_number), "Lokasi", format2)
            sheet.write('I'+str(row_number), "Qty", format2)
            sheet.write('J'+str(row_number), "OAT", format2)
            sheet.write('K'+str(row_number), "Total", format2)
            sheet.write('L'+str(row_number), "Pemakaian", format2)
            sheet.write('M'+str(row_number), "Fee", format2)
            sheet.write('N'+str(row_number), "Pendapatan", format2)
            sheet.write('O'+str(row_number), "SO Sistem", format2)
            row_number += 1
            
            for line in datas[customer]:
                sheet.write('A'+str(row_number), line['date'], format6)
                sheet.write('B'+str(row_number), line['order_number'], format5)
                sheet.write('C'+str(row_number), line['delivery_number'], format5)
                sheet.write('D'+str(row_number), line['travel'], format5)
                sheet.write('E'+str(row_number), line['driver'], format5)
                sheet.write('F'+str(row_number), line['plate'], format5)
                sheet.write('G'+str(row_number), line['destination'], format5)
                sheet.write('H'+str(row_number), line['location'], format5)
                sheet.write('I'+str(row_number), line['qty'], format5)
                sheet.write('J'+str(row_number), line['oat'], format5)
                sheet.write('K'+str(row_number), line['total'], format5)
                sheet.write('L'+str(row_number), line['solar_usage'], format5)
                sheet.write('M'+str(row_number), line['fee'], format5)
                sheet.write('N'+str(row_number), line['income'], format5)
                sheet.write('O'+str(row_number), line['order'], format5)
                row_number += 1


    def generate_report(self, start_date=False, end_date=False, customer_ids=False):
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
        datas = {}

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
                ])
                for delivery in deliveries:
                    already = True
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
                        'destination': (partner.parent_id.name or ''),
                        'location': (partner.street or '') + ' ' + (partner.city or ''),
                        'qty': vehicle.capacity_id.name,
                        'oat': order.amount_total/int(vehicle.capacity_id.name),
                        'total': order.amount_total,
                        'solar_usage': delivery.fuel_id.amount or 0,
                        'fee': fee or 0,
                        'income': order.amount_total - fee,
                        'order': order.name,
                    }

                    if customer.name in datas:
                        datas[customer.name].append(data)
                    else:
                        datas[customer.name] = [data]

                if not already:
                    qty = order.order_line[0].product_uom_qty
                    data = {
                        'date': order.delivery_date,
                        'order_number': order.order_number,
                        'delivery_number': order.delivery_number,
                        'travel': '-',
                        'driver': '-',
                        'plate': '-',
                        'destination': (partner.parent_id.name or ''),
                        'location': (partner.street or '') + ' ' + (partner.city or ''),
                        'qty': qty,
                        'oat': order.amount_total/int(vehicle.capacity_id.name),
                        'total': order.amount_total,
                        'solar_usage': 0,
                        'fee': 0,
                        'income': order.amount_total,
                        'order': order.name,
                    }
                    if customer.name in datas:
                        datas[customer.name].append(data)
                    else:
                        datas[customer.name] = [data]
        
        return datas