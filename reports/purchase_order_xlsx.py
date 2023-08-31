from odoo.http import request
from odoo import fields, models, api, _
from datetime import datetime
from io import BytesIO
import base64

import pytz

import logging
_logger = logging.getLogger(__name__)

class PurchaseOrderReportXlsx(models.AbstractModel):
    _name = 'report.custom_report_purchase.report_purchase_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        ids = data['ids']
        orders = self.env['purchase.order'].search([ ('id', 'in', ids) ])
        company = orders[0].user_id.company_id

        sheet = workbook.add_worksheet("Purchase Order")

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
        format4.set_align('right')
        format4.set_align('vcenter')
        format_header_cell_color = workbook.add_format({'font_size':11, 'bold': True, 'bg_color': '#D9E1F2'})
        format_header_cell_color.set_align('center')
        format_header_cell_color.set_align('vcenter')
        format_header_cell_color.set_border()
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

        sheet.merge_range(0, 3, 0, 6, company.name, format1)
        sheet.merge_range(1, 3, 1, 6, company.street, format2)
        sheet.merge_range(2, 3, 2, 6, company.street2, format2)
        sheet.merge_range(3, 3, 3, 6, company.city + ' ' + company.state_id.name + ' ' + company.zip, format2)
        sheet.merge_range(4, 3, 4, 6, company.country_id.name, format2)

        sheet.merge_range(6, 0, 6, 1, 'Purchase Order', format3)
        sheet.merge_range(6, 3, 6, 6, data['date'], format4)

        row = 8
        for order in orders:
            sheet.merge_range(row, 0, row, 6, order.partner_id.name + ' (' + order.name + ')', format_header_cell_color)
            sheet.merge_range(row+1, 0, row+2, 6, order.notes or '', format_cell_left)
            
            # header table
            row += 3
            sheet.write(row, 0, 'No', format_header_cell_center)
            sheet.write(row, 1, 'Produk', format_header_cell_center)
            sheet.write(row, 2, 'Kendaraan', format_header_cell_center)
            sheet.write(row, 3, 'Qty', format_header_cell_center)
            sheet.write(row, 4, 'Pajak', format_header_cell_center)
            sheet.write(row, 5, 'Harga Satuan (Rp)', format_header_cell_right)
            sheet.write(row, 6, 'Total (Rp)', format_header_cell_right)
            row += 1

            # line
            number = 1
            for line in order.order_line:
                sheet.write(row, 0, number, format_cell_center)
                sheet.write(row, 1, line.name, format_cell_left)
                sheet.write(row, 2, line.vehicle_id.name or '', format_cell_left)
                sheet.write(row, 3, str(line.product_qty) + ' ' + line.product_uom.name, format_cell_left)
                sheet.write(row, 4, line.taxes_id.name or '', format_cell_left)
                sheet.write(row, 5, line.price_unit, format_cell_right)
                sheet.write(row, 6, line.price_subtotal, format_cell_right)
                row += 1
                number += 1
            
            sheet.merge_range(row, 0, row, 6, '', format3)
            row += 1

        row += 2
        sheet.merge_range(row, 0, row, 1, 'Dibuat Oleh', format_header_cell_center)
        sheet.merge_range(row, 2, row, 3, 'Dibayar Oleh', format_header_cell_center)
        sheet.merge_range(row, 4, row, 5, 'Disetujui Oleh', format_header_cell_center)
        sheet.write(row, 6, 'Mengetahui', format_header_cell_center)
        row += 1
        sheet.merge_range(row, 0, row+6, 1, '', format_header_cell_center)
        sheet.merge_range(row, 2, row+6, 3, '', format_header_cell_center)
        sheet.merge_range(row, 4, row+6, 5, '', format_header_cell_center)
        sheet.merge_range(row, 6, row+6, 6, '', format_header_cell_center)
        row += 7
        sheet.merge_range(row, 0, row, 1, order.user_id.name, format_header_cell_center)
        sheet.merge_range(row, 2, row, 3, '', format_header_cell_center)
        sheet.merge_range(row, 4, row, 5, 'Dedy Kurniawan', format_header_cell_center)
        sheet.write(row, 6, 'Alpianus D.M', format_header_cell_center)
        row += 1
        sheet.merge_range(row, 0, row, 1, 'Admin Pembelian', format_header_cell_center)
        sheet.merge_range(row, 2, row, 3, 'Accounting', format_header_cell_center)
        sheet.merge_range(row, 4, row, 5, 'Manager', format_header_cell_center)
        sheet.write(row, 6, 'Owner', format_header_cell_center)
