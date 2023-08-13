from odoo import fields, models, api, _
from datetime import timedelta

import pytz

import logging
_logger = logging.getLogger(__name__)

class InvoiceCustomerReport(models.AbstractModel):
    _name = "report.report_invoice.report_invoice_customer"
    _description = "Report Invoice Customer"

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

        datas = {}

        for customer in customer_ids:
            invoices = self.env['account.invoice'].search([
                ('partner_id.id', '=', customer.id),
                ('type', '=', 'out_invoice'),
                ('state', '=', 'open'),
                ('date_invoice', '>=', start_date),
                ('date_invoice', '<=', end_date),
            ], order='date_invoice ASC')
            for invoice in invoices:
                price_unit = qty = 0
                for line in invoice.invoice_line_ids:
                    price_unit = line.price_unit
                    is_prod_del = self.env['setting.product.pricelist'].search([ ('product_id', '=', line.product_id.product_tmpl_id.id) ])
                    if is_prod_del: qty += line.quantity

                destination = location = ''
                if invoice.origin: 
                    order = self.env['sale.order'].search([ ('name', '=', invoice.origin) ], limit=1)
                    if order.partner_shipping_id:
                        destination = order.partner_shipping_id.parent_id.name or ''
                        location = order.partner_shipping_id.name or ''
                        price_unit = order.partner_shipping_id.parent_id.oat

                

                data = {
                    'date': invoice.date_invoice,
                    'number': invoice.number,
                    'customer': destination,
                    'location': location,
                    'unit_price': price_unit,
                    'qty': str(int(qty)),
                    'amount': invoice.amount_total,
                }
                if customer.name in datas:
                    datas[customer.name].append(data)
                else:
                    datas[customer.name] = [data]
        
        return {
            'currency_precision': user_currency.decimal_places,
            'datas': datas,
            'start_date': start_date,
            'end_date': end_date,
        }

    @api.multi
    def _get_report_values(self, docids, data=None):
        data = dict(data or {})
        customer_ids = self.env['res.partner'].browse(data['customer_ids'])
        data.update(self.get_report(data['start_date'], data['end_date'], customer_ids))
        return data