from odoo import fields, models, api, _
from odoo.exceptions import UserError
from num2words import num2words
import roman
from io import BytesIO
import base64

import logging
_logger = logging.getLogger(__name__)

class PRInvoiceCustomerReportXlsx(models.AbstractModel):
    _name = 'report.pr_invoice.report_pr_account_invoice_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        company = self.env['res.company'].search([ ('id', '=', data['company_id']) ])
        document = self.env['pr.account.invoice'].search([ ('id', '=', data['doc_id']) ])

        sheet = workbook.add_worksheet("PAYMENT REQUEST VENDOR BILLS")

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
        format5 = workbook.add_format({'font_size': 12, 'bold': True})
        format5.set_align('center')
        format5.set_align('vcenter')
        format_header_cell_left = workbook.add_format({'font_size':11, 'bold': True})
        format_header_cell_left.set_align('left')
        format_header_cell_left.set_align('vcenter')
        format_header_cell_left.set_border()
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

        sheet.merge_range(0, 2, 0, 5, company.name, format1)
        sheet.merge_range(1, 2, 1, 5, company.street, format2)
        sheet.merge_range(2, 2, 2, 5, company.street2, format2)
        sheet.merge_range(3, 2, 3, 5, company.city + ' ' + company.state_id.name + ' ' + company.zip, format2)
        sheet.merge_range(4, 2, 4, 5, company.country_id.name, format2)
        
        sheet.merge_range(6, 0, 6, 5, "PAYMENT REQUEST VENDOR BILLS " + document.name, format5)
        sheet.merge_range(7, 0, 7, 5, document.start_date.strftime('%d-%m-%Y') + ' sampai ' + document.end_date.strftime('%d-%m-%Y'), format_cell_center)
        
        row = 9

        if data['type'] == 'recap':
            row += 1
            sheet.write(row, 0, "No", format_header_cell_center)
            sheet.write(row, 1, "Vendor", format_header_cell_center)
            sheet.write(row, 2, "Tagihan", format_header_cell_center)
            sheet.write(row, 3, "Tanggal", format_header_cell_center)
            sheet.write(row, 4, "Total (Rp)", format_header_cell_right)
            sheet.write(row, 5, "Sisa (Rp)", format_header_cell_right)
            row += 1
        
        number = 1
        total = 0
        for line in document.line_ids:
            if data['type'] == 'detail':
                row += 1
                sheet.write(row, 0, "No", format_header_cell_center)
                sheet.write(row, 1, "Vendor", format_header_cell_center)
                sheet.write(row, 2, "Tagihan", format_header_cell_center)
                sheet.write(row, 3, "Tanggal", format_header_cell_center)
                sheet.write(row, 4, "Total (Rp)", format_header_cell_right)
                sheet.write(row, 5, "Sisa (Rp)", format_header_cell_right)
                row += 1

            sheet.write(row, 0, number, format_cell_center)
            sheet.write(row, 1, line.bill_id.partner_id.name, format_cell_center)
            sheet.write(row, 2, line.bill_id.number, format_cell_center)
            sheet.write(row, 3, line.bill_id.date_invoice.strftime('%d-%m-%Y'), format_cell_center)
            sheet.write(row, 4, line.bill_id.amount_total, format_cell_right)
            sheet.write(row, 5, line.bill_id.residual, format_cell_right)
            row += 1
            
            if data['type'] == 'detail':
                row += 1
                sheet.write(row, 0, "Produk", format_header_cell_center)
                sheet.write(row, 1, "Qty", format_header_cell_center)
                sheet.write(row, 2, "UoM", format_header_cell_center)
                sheet.write(row, 3, "Harga (Rp)", format_header_cell_right)
                sheet.write(row, 4, "Pajak", format_header_cell_center)
                sheet.write(row, 5, "Total (Rp)", format_header_cell_right)
                row += 1
                for bill_line in line.bill_id.invoice_line_ids:
                    sheet.write(row, 0, bill_line.product_id.name, format_cell_center)
                    sheet.write(row, 1, bill_line.quantity, format_cell_center)
                    sheet.write(row, 2, bill_line.uom_id.name, format_cell_center)
                    sheet.write(row, 3, bill_line.price_unit, format_cell_right)
                    sheet.write(row, 4, bill_line.invoice_line_tax_ids.name or '', format_cell_center)
                    sheet.write(row, 5, bill_line.price_subtotal, format_cell_right)
                    row += 1

                row += 2

            if data['type'] == 'recap':
                number += 1
            total += line['amount']
        
        row += 1
        sheet.merge_range(row, 0, row, 4, 'Total (Rp)', format_cell_left)
        sheet.write(row, 5, total, format_cell_right)