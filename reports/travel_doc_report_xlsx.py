from odoo.http import request
from odoo import fields, models, api, _
from odoo.exceptions import UserError
from num2words import num2words
import roman
from io import BytesIO
import base64

import pytz

import logging
_logger = logging.getLogger(__name__)

class TravelDocReportXlsx(models.AbstractModel):
    _name = 'report.custom_delivery.report_travel_doc_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        delivery_id = data['data'][54:-9]
        if not delivery_id: raise UserError(_("Can't Print Document"))

        document = self.env['delivery.driver'].search([ ('id', '=', delivery_id) ])
        # get qty delivery
        qty = 0
        qty_str = ''
        for line in document.order_id.order_line:
            # product delivery
            is_prod_del = self.env['setting.product.pricelist'].search([ ('product_id', '=', line.product_id.product_tmpl_id.id) ])
            if is_prod_del:
                qty += line.product_uom_qty
        qty_str = num2words(int(qty), lang="id")

        # vehicle
        vehicle = document.vehicle_id
        if len(document.change_vehicle_ids) > 0:
            vehicle = document.change_vehicle_ids[len(document.change_vehicle_ids)-1].vehicle_id
        # get gauge tank
        gauge_tank = self.env['fleet.gauge.tank.log'].search([
            ('vehicle_id.id', '=', vehicle.id),
        ], limit=1, order='id desc')
        # seal number
        seal_number_ids = document.seal_number_ids
        if len(document.change_vehicle_ids) > 0:
            seal_number_ids = document.change_vehicle_ids[len(document.change_vehicle_ids)-1].seal_number_ids

        top_seal = []
        bottom_seal = []
        for line in seal_number_ids:
            if line.position == 'top':
                for seal in line.seal_ids:
                    top_seal.append(seal.name)
            if line.position == 'bottom':
                for seal in line.seal_ids:
                    bottom_seal.append(seal.name) 

        dt = {
            'company': {
                'name': document.company_id.name,
                'address': document.company_id.street,
                'address_short': document.company_id.street + ' ' + str(document.company_id.city or ''),
                'city': str(document.company_id.city or '') + ' ' + str(document.company_id.state_id.name or ''),
                'vat': document.company_id.vat,
            },
            'destination': {
                'name': str(document.order_id.partner_shipping_id.parent_id.name or ''),
                'address': str(document.order_id.partner_shipping_id.name or ''),
                'customer_ref': str(document.order_id.client_order_ref or ''),
                'vat': str(document.order_id.partner_shipping_id.parent_id.vat or ''),
            },
            'doc': {
                'travel_number': 'No Surat Jalan    : SJ/NMS/' + roman.toRoman(document.delivery_date.month) + '/' + document.name[-4:],
                'delivery_number': 'No. DO               : ' + document.order_id.delivery_number,
                'order_number': 'No. SO               : ' + document.order_id.order_number,
                'effective_date': document.delivery_date.strftime('%d') + ' s/d ' + document.end_date.strftime('%d/%m/%Y'),
                'product': {
                    'name': str(document.order_id.product_delivery_id.name or ''),
                    'qty': str(int(qty)) + " L",
                    'countable_qty': qty_str.upper() + ' LITER',
                },
                'vehicle': {
                    'type': str(vehicle.model_id.name),
                    'plate': str(vehicle.license_plate),
                    'gauge_tank': str(gauge_tank.value or 0),
                    'top_seal': 'Segel Atas ' + '%s' % (', '.join(top_seal)),
                    'bottom_seal': 'Segel Bawah ' + '%s' % (', '.join(bottom_seal)),
                    'driver': str(document.driver_id.name),
                },
                'date': document.delivery_date.strftime('%d/%m/%Y'),
                'publisher': str(document.order_id.user_id.name),
                'director': 'DEDY KURNIAWAN',
            }
        }



        sheet = workbook.add_worksheet("Surat Jalan")

        # format
        format1 = workbook.add_format({'font_size': 28, 'bold': True})
        format1.set_align('center')
        format1.set_align('vcenter')
        format2 = workbook.add_format({'font_size': 12, 'bold': True})
        format3 = workbook.add_format({'font_size': 12})
        format4 = workbook.add_format({'font_size': 12})
        format4.set_bottom(6)
        format5 = workbook.add_format({'font_size': 12, 'bg_color': '#D9E1F2'})
        format5.set_align('center')
        format5.set_align('vcenter')
        format5.set_border()
        format6 = workbook.add_format({'font_size': 12})
        format6.set_align('center')
        format6.set_align('vcenter')
        format6.set_border()
        format7 = workbook.add_format({'font_size': 12, 'font_color':'red'})
        format7.set_align('center')
        format7.set_align('vcenter')
        format7.set_border()
        format8 = workbook.add_format({'font_size': 12})
        format8.set_border()
        format9 = workbook.add_format({'font_size': 12, 'bold': True})
        format9.set_align('center')
        format9.set_align('vcenter')
        format9.set_border()
        
        
        # image
        logo = BytesIO(base64.b64decode(document.company_id.logo_icon))
        sheet.insert_image("A2", "logo.png", {'image_data': logo, 'x_offset': 15, 'y_offset': 0})
        sheet.insert_image("A24", "logo.png", {'image_data': logo, 'x_offset': 15, 'y_offset': 0})

        signature = BytesIO(base64.b64decode(document.company_id.signature))
        sheet.insert_image("C19", "signature.png", {'image_data': signature, 'x_offset': 15, 'y_offset': 15})
        sheet.insert_image("C41", "signature.png", {'image_data': signature, 'x_offset': 15, 'y_offset': 15})
        
        # set height
        sheet.set_default_row(15.01)
        sheet.set_row(1, 65.60)
        sheet.set_row(2, 17.8)
        sheet.set_row(3, 17.8)
        sheet.set_row(4, 17.8)
        sheet.set_row(11, 16.85)
        sheet.set_row(12, 16.85)
        sheet.set_row(13, 16.85)
        sheet.set_row(14, 16.85)
        sheet.set_row(15, 16.85)
        sheet.set_row(16, 23)
        sheet.set_row(18, 73.10)
        sheet.set_row(23, 65.60)
        sheet.set_row(24, 17.8)
        sheet.set_row(25, 17.8)
        sheet.set_row(26, 17.8)
        sheet.set_row(33, 16.85)
        sheet.set_row(34, 16.85)
        sheet.set_row(35, 16.85)
        sheet.set_row(36, 16.85)
        sheet.set_row(37, 16.85)
        sheet.set_row(38, 23)
        sheet.set_row(40, 73.10)

        # set width
        sheet.set_column('A:A', 14.84)
        sheet.set_column('B:B', 11.88)
        sheet.set_column('C:C', 8.23)
        sheet.set_column('D:D', 8.38)
        sheet.set_column('E:E', 19.66)
        sheet.set_column('F:F', 12.80)
        sheet.set_column('G:G', 25.80)
        sheet.set_column('H:H', 3.94)
        sheet.set_column('I:I', 8.38)
        sheet.set_column('J:J', 12.52)
        
        sheet.merge_range(0, 0, 1, 9, "SURAT JALAN", format1)

        sheet.merge_range(2, 0, 2, 4, dt['company']['name'], format2)
        sheet.merge_range(3, 0, 3, 4, dt['company']['address'], format3)
        sheet.merge_range(4, 0, 4, 4, dt['company']['city'], format4)
        sheet.merge_range(2, 5, 2, 9, dt['doc']['travel_number'], format3)
        sheet.merge_range(3, 5, 3, 9, dt['doc']['delivery_number'], format3)
        sheet.merge_range(4, 5, 4, 9, dt['doc']['order_number'], format4)

        sheet.merge_range(5, 0, 5, 4, 'Kepada       : ' + dt['destination']['name'], format3)
        sheet.merge_range(6, 0, 6, 4, 'Alamat        : ' + dt['destination']['address'], format3)
        sheet.merge_range(7, 0, 7, 4, 'No PO        : ' + dt['destination']['customer_ref'], format3)
        sheet.merge_range(8, 0, 8, 4, 'N.P.W.P     : ' + dt['destination']['vat'], format3)
        sheet.merge_range(5, 5, 5, 9, 'Tanggal              : ' + dt['doc']['date'], format3)
        sheet.merge_range(6, 5, 6, 9, 'Agen/Transportir  : ' + dt['company']['name'], format3)
        sheet.merge_range(7, 5, 7, 9, 'Alamat                : ' + dt['company']['address_short'], format3)
        sheet.merge_range(8, 5, 8, 9, 'N.P.W.P             : ' + dt['company']['vat'], format3)

        sheet.merge_range(9, 0, 9, 2, "Tanggal Berlaku", format5)
        sheet.merge_range(10, 0, 10, 2, dt['doc']['effective_date'], format6)
        sheet.merge_range(9, 3, 9, 5, "Produk", format5)
        sheet.merge_range(10, 3, 10, 5, dt['doc']['product']['name'], format6)
        sheet.merge_range(9, 6, 9, 9, "Kuantitas", format5)
        sheet.merge_range(10, 6, 10, 9, dt['doc']['product']['qty'], format6)

        sheet.merge_range(11, 0, 12, 0, "Dikirim Dengan ", format6)
        sheet.merge_range(11, 1, 12, 2, dt['doc']['vehicle']['type'], format6)
        sheet.merge_range(11, 3, 12, 5, dt['doc']['vehicle']['top_seal'], format7)
        sheet.merge_range(11, 6, 11, 7, "Waktu Muat", format8)
        sheet.merge_range(12, 6, 12, 7, "Waktu Bongkar", format8)
        sheet.merge_range(11, 8, 11, 9, "", format8)
        sheet.merge_range(12, 8, 12, 9, "", format8)

        sheet.merge_range(13, 0, 14, 0, "No Kendaraan", format6)
        sheet.merge_range(13, 1, 14, 2, dt['doc']['vehicle']['plate'], format6)
        sheet.merge_range(13, 3, 14, 5, dt['doc']['vehicle']['bottom_seal'], format7)
        sheet.merge_range(13, 6, 13, 7, "KM Muat", format8)
        sheet.merge_range(14, 6, 14, 7, "KM Bongkar", format8)
        sheet.merge_range(13, 8, 13, 9, "", format8)
        sheet.merge_range(14, 8, 14, 9, "", format8)

        sheet.write(15, 0, "SG Meter", format8)
        sheet.merge_range(15, 1, 15, 2, dt['doc']['vehicle']['gauge_tank'], format6)
        sheet.merge_range(15, 3, 15, 5, "", format8)
        sheet.merge_range(15, 6, 15, 7, "KM Akhir", format8)
        sheet.merge_range(15, 8, 15, 9, "", format8)
        
        sheet.write(16, 0, "Jumlah (Liter)", format8)
        sheet.merge_range(16, 1, 16, 9, dt['doc']['product']['countable_qty'], format9)

        sheet.merge_range(17, 0, 17, 1, "Dibuat Oleh", format5)
        sheet.merge_range(17, 2, 17, 4, "Mengetahui", format5)
        sheet.merge_range(17, 5, 17, 6, "Penerima", format5)
        sheet.merge_range(17, 7, 17, 9, "Pengemudi", format5)

        sheet.merge_range(18, 0, 18, 1, "", format6)
        sheet.merge_range(18, 2, 18, 4, "", format6)
        sheet.merge_range(18, 5, 18, 6, "", format6)
        sheet.merge_range(18, 7, 18, 9, "", format6)

        sheet.merge_range(19, 0, 20, 1, dt['doc']['publisher'], format9)
        sheet.merge_range(19, 2, 20, 4, dt['doc']['director'], format9)
        sheet.merge_range(19, 5, 20, 6, dt['destination']['name'], format9)
        sheet.merge_range(19, 7, 20, 9, dt['doc']['vehicle']['driver'], format9)
        
        
        sheet.merge_range(21, 0, 21, 9, "", format6)

        sheet.merge_range(22, 0, 23, 9, "SURAT JALAN", format1)

        sheet.merge_range(24, 0, 24, 4, dt['company']['name'], format2)
        sheet.merge_range(25, 0, 25, 4, dt['company']['address'], format3)
        sheet.merge_range(26, 0, 26, 4, dt['company']['city'], format4)
        sheet.merge_range(24, 5, 24, 9, dt['doc']['travel_number'], format3)
        sheet.merge_range(25, 5, 25, 9, dt['doc']['delivery_number'], format3)
        sheet.merge_range(26, 5, 26, 9, dt['doc']['order_number'], format4)

        sheet.merge_range(27, 0, 27, 4, 'Kepada       : ' + dt['destination']['name'], format3)
        sheet.merge_range(28, 0, 28, 4, 'Alamat        : ' + dt['destination']['address'], format3)
        sheet.merge_range(29, 0, 29, 4, 'No PO        : ' + dt['destination']['customer_ref'], format3)
        sheet.merge_range(30, 0, 30, 4, 'N.P.W.P     : ' + dt['destination']['vat'], format3)
        sheet.merge_range(27, 5, 27, 9, 'Tanggal              : ' + dt['doc']['date'], format3)
        sheet.merge_range(28, 5, 28, 9, 'Agen/Transportir  : ' + dt['company']['name'], format3)
        sheet.merge_range(29, 5, 29, 9, 'Alamat                : ' + dt['company']['address_short'], format3)
        sheet.merge_range(30, 5, 30, 9, 'N.P.W.P             : ' + dt['company']['vat'], format3)

        sheet.merge_range(31, 0, 31, 2, "Tanggal Berlaku", format5)
        sheet.merge_range(32, 0, 32, 2, dt['doc']['effective_date'], format6)
        sheet.merge_range(31, 3, 31, 5, "Produk", format5)
        sheet.merge_range(32, 3, 32, 5, dt['doc']['product']['name'], format6)
        sheet.merge_range(31, 6, 31, 9, "Kuantitas", format5)
        sheet.merge_range(32, 6, 32, 9, dt['doc']['product']['qty'], format6)

        sheet.merge_range(33, 0, 34, 0, "Dikirim Dengan ", format6)
        sheet.merge_range(33, 1, 34, 2, dt['doc']['vehicle']['type'], format6)
        sheet.merge_range(33, 3, 34, 5, dt['doc']['vehicle']['top_seal'], format7)
        sheet.merge_range(33, 6, 33, 7, "Waktu Muat", format8)
        sheet.merge_range(34, 6, 34, 7, "Waktu Bongkar", format8)
        sheet.merge_range(33, 8, 33, 9, "", format8)
        sheet.merge_range(34, 8, 34, 9, "", format8)

        sheet.merge_range(35, 0, 36, 0, "No Kendaraan", format6)
        sheet.merge_range(35, 1, 36, 2, dt['doc']['vehicle']['plate'], format6)
        sheet.merge_range(35, 3, 36, 5, dt['doc']['vehicle']['bottom_seal'], format7)
        sheet.merge_range(35, 6, 35, 7, "KM Muat", format8)
        sheet.merge_range(36, 6, 36, 7, "KM Bongkar", format8)
        sheet.merge_range(35, 8, 35, 9, "", format8)
        sheet.merge_range(36, 8, 36, 9, "", format8)

        sheet.write(37, 0, "SG Meter", format8)
        sheet.merge_range(37, 1, 37, 2, dt['doc']['vehicle']['gauge_tank'], format6)
        sheet.merge_range(37, 3, 37, 5, "", format8)
        sheet.merge_range(37, 6, 37, 7, "KM Akhir", format8)
        sheet.merge_range(37, 8, 37, 9, "", format8)
        
        sheet.write(38, 0, "Jumlah (Liter)", format8)
        sheet.merge_range(38, 1, 38, 9, dt['doc']['product']['countable_qty'], format9)

        sheet.merge_range(39, 0, 39, 1, "Made by", format5)
        sheet.merge_range(39, 2, 39, 4, "Mengetahui", format5)
        sheet.merge_range(39, 5, 39, 6, "Penerima", format5)
        sheet.merge_range(39, 7, 39, 9, "Pengemudi", format5)

        sheet.merge_range(40, 0, 40, 1, "", format6)
        sheet.merge_range(40, 2, 40, 4, "", format6)
        sheet.merge_range(40, 5, 40, 6, "", format6)
        sheet.merge_range(40, 7, 40, 9, "", format6)

        sheet.merge_range(41, 0, 42, 1, dt['doc']['publisher'], format9)
        sheet.merge_range(41, 2, 42, 4, dt['doc']['director'], format9)
        sheet.merge_range(41, 5, 42, 6, dt['destination']['name'], format9)
        sheet.merge_range(41, 7, 42, 9, dt['doc']['vehicle']['driver'], format9)
        
        sheet.merge_range(43, 0, 43, 9, "", format6)
