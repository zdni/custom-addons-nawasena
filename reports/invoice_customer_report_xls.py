from odoo import fields, models, _
from io import BytesIO
import base64

import logging
_logger = logging.getLogger(__name__)

class InvoiceCustomerReportXls(models.AbstractModel):
    _name = 'report.report_invoice.report_invoice_customer_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        
        start_date = data['start_date']
        end_date = data['end_date']
        customer_ids = data['customer_ids']
        company = self.env['res.company'].search([ ('id', '=', data['company_id']) ])

        datas = self.generate_report(start_date, end_date, customer_ids)

        sheet = workbook.add_worksheet("Report Invoice Customer")

        # format
        format1 = workbook.add_format({'font_size': 12, 'bold': True})
        format1.set_align('right')
        format1.set_align('vcenter')
        format2 = workbook.add_format({'font_size': 10})
        format2.set_align('right')
        format2.set_align('vcenter')
        format3 = workbook.add_format({'font_size': 11, 'bold': True})
        format3.set_align('left')
        format3.set_align('vcenter')
        format4 = workbook.add_format({'font_size': 11, 'bold': True})
        format4.set_align('left')
        format4.set_align('vcenter')
        format5 = workbook.add_format({'font_size': 12, 'bold': True})
        format5.set_align('center')
        format5.set_align('vcenter')
        format_header_cell_center = workbook.add_format({'font_size':11, 'bold': True})
        format_header_cell_center.set_align('center')
        format_header_cell_center.set_align('vcenter')
        format_header_cell_center.set_border()
        format_header_cell_right = workbook.add_format({'font_size':11, 'bold': True})
        format_header_cell_right.set_align('right')
        format_header_cell_right.set_align('vcenter')
        format_header_cell_right.set_border()
        format_cell_left = workbook.add_format({'font_size':10})
        format_cell_left.set_align('left')
        format_cell_left.set_align('vcenter')
        format_cell_left.set_border()
        format_cell_center = workbook.add_format({'font_size':10})
        format_cell_center.set_align('center')
        format_cell_center.set_align('vcenter')
        format_cell_center.set_border()
        format_cell_right = workbook.add_format({'font_size':10, 'num_format': '#,###'})
        format_cell_right.set_align('right')
        format_cell_right.set_align('vcenter')
        format_cell_right.set_border()
        
        # image
        logo = BytesIO(base64.b64decode(company.logo))
        sheet.insert_image("A1", "logo.png", {'image_data': logo, 'x_offset': 15, 'y_offset': 15, 'x_scale': 0.6, 'y_scale': 0.6})

        sheet.merge_range(0, 4, 0, 7, company.name, format1)
        sheet.merge_range(1, 4, 1, 7, company.street, format2)
        sheet.merge_range(2, 4, 2, 7, company.street2, format2)
        sheet.merge_range(3, 4, 3, 7, company.city + ' ' + company.state_id.name + ' ' + company.zip, format2)
        sheet.merge_range(4, 4, 4, 7, company.country_id.name, format2)
        
        sheet.merge_range(6, 0, 6, 7, "LAPORAN TAGIHAN PELANGGAN", format5)
        sheet.merge_range(7, 0, 7, 7, start_date + ' sampai ' + end_date, format_cell_center)
        
        row = 9
        for customer in datas.keys():
            sheet.merge_range(row, 0, row, 7, customer, format4)

            row += 1
            sheet.write(row, 0, "No", format_header_cell_center)
            sheet.write(row, 1, "Tanggal", format_header_cell_center)
            sheet.write(row, 2, "Tagihan", format_header_cell_center)
            sheet.write(row, 3, "Tujuan", format_header_cell_center)
            sheet.write(row, 4, "Lokasi", format_header_cell_center)
            sheet.write(row, 5, "Qty", format_header_cell_right)
            sheet.write(row, 6, "Harga", format_header_cell_right)
            sheet.write(row, 7, "Total", format_header_cell_right)
            row += 1
            
            number = 1
            total = 0
            for line in datas[customer]:
                sheet.write(row, 0, number, format_cell_center)
                sheet.write(row, 1, line['date'], format_cell_center)
                sheet.write(row, 2, line['number'], format_cell_center)
                sheet.write(row, 3, line['customer'], format_cell_center)
                sheet.write(row, 4, line['location'], format_cell_center)
                sheet.write(row, 5, line['unit_price'], format_cell_right)
                sheet.write(row, 6, line['qty'], format_cell_right)
                sheet.write(row, 7, line['amount'], format_cell_right)
                row += 1
                number += 1
                total += line['amount']

            sheet.merge_range(row, 0, row, 6, 'Total (Rp)', format_cell_left)
            sheet.write(row, 7, total, format_cell_right)
            row += 1
            sheet.merge_range(row, 0, row, 7, '', format3)
            row += 1


    def generate_report(self, start_date=False, end_date=False, customer_ids=False):
        if not customer_ids:
            customer_ids = self.env['res.partner'].search([ ('customer', '=', True) ])
        
        if start_date:
            start_date = fields.Datetime.from_string(start_date)

        if end_date:
            end_date = fields.Datetime.from_string(end_date)
         
        end_date = max(end_date, start_date)

        start_date = fields.Datetime.to_string(start_date)
        end_date = fields.Datetime.to_string(end_date)

        datas = {}

        for customer in customer_ids:
            customer_name = customer.parent_id.name if customer.parent_id else customer.name
            
            invoices = self.env['account.invoice'].search([
                ('partner_id.id', '=', customer.id),
                ('type', '=', 'out_invoice'),
                ('state', '=', 'open'),
                ('date_invoice', '>=', start_date),
                ('date_invoice', '<=', end_date),
            ], order='date_invoice ASC')
            for invoice in invoices:
                if invoice.origin:
                    order_ids = [name.strip() for name in invoice.origin.split(',')]
                    orders = self.env['sale.order'].search([ ('name', 'in', order_ids) ])
                    for order in orders:
                        destination = order.partner_shipping_id.parent_id.name or ''
                        location = order.partner_shipping_id.name or ''
                        price_unit = order.order_line[0].price_unit or 0
                        qty = order.order_line[0].product_uom_qty or 0
                        data = {
                            'date': invoice.date_invoice,
                            'number': invoice.number,
                            'customer': destination,
                            'location': location,
                            'unit_price': price_unit,
                            'qty': str(int(qty)),
                            'amount': order.amount_total,
                        }
                        if customer_name in datas:
                            datas[customer_name].append(data)
                        else:
                            datas[customer_name] = [data]
                else:
                    price_unit = invoice.invoice_line_ids[0].price_unit or 0
                    qty = invoice.invoice_line_ids[0].quantity or 0
                    destination = invoice.partner_shipping_id.parent_id.name or invoice.partner_shipping_id.name
                    location = invoice.partner_shipping_id.name if invoice.partner_shipping_id.parent_id else ''

                    data = {
                        'date': invoice.date_invoice,
                        'number': invoice.number,
                        'customer': destination,
                        'location': location,
                        'unit_price': price_unit,
                        'qty': str(int(qty)),
                        'amount': invoice.amount_total,
                    }
                    if customer_name in datas:
                        datas[customer_name].append(data)
                    else:
                        datas[customer_name] = [data]
        
        return datas