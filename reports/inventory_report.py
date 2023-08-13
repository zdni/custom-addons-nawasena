from odoo import fields, models, api, _
from datetime import timedelta

import logging
_logger = logging.getLogger(__name__)

class InventoryReport(models.AbstractModel):
    _name = "report.stock_card.report_inventory"
    _description = "Report Inventory"

    @api.model
    def get_report(self, start_date=False, end_date=False, product_ids=False):
        user_currency = self.env.user.company_id.currency_id
        StockCardLine = self.env['stock.card.line']

        if not product_ids:
            product_ids = self.env['product.product'].search([])
        
        if start_date:
            start_date_obj = fields.Datetime.from_string(start_date)

        if end_date:
            end_date_obj = fields.Datetime.from_string(end_date)
            end_date_obj = end_date_obj + timedelta(days=1, seconds=-1)
        
        _logger.warning(start_date_obj)         
        start_date_str = fields.Datetime.to_string(start_date_obj)
        end_date_str = fields.Datetime.to_string(end_date_obj)

        datas = {}

        for product in product_ids:
            StockCardLine.process( product.id )
            
            lines = StockCardLine.search([
                ('product_id.id', '=', product.id),
                ('date', '>=', start_date_obj),
                ('date', '<=', end_date_obj),
            ], order='date ASC, id ASC')
            for line in lines:
                moves = self.env['account.move'].search([ ('id', 'in', line.move_id.account_move_ids.ids) ])
                amount = sum(move.amount for move in moves)
                
                value = line.qty_in if line.qty_in else line.qty_out

                notes = 'SARLUN'
                if line.move_id.location_dest_id.usage == 'inventory' or line.move_id.location_id.usage == 'inventory':
                    fuel = self.env['fleet.vehicle.log.fuel'].search([ ('inv_adj_id.id', '=', line.move_id.inventory_id.id) ], limit=1)
                    # notes = fuel.vehicle_id.name or '-'
                    notes = fuel.vehicle_id.driver_id.name or 'SARLUN'

                data = { 
                    'date': line.date, 
                    'notes': notes,
                    'information': line.information, 
                    'qty_start': line.qty_start,
                    'qty_in': line.qty_in,
                    'qty_out': line.qty_out,
                    'qty_balance': line.qty_balance,
                    'price': amount/value,
                    'amount': amount, 
                    'real_amount': amount if line.qty_in else amount*-1
                }

                if product.name in datas:
                    datas[product.name].append(data)
                else:
                    datas[product.name] = [data]

        return {
            'currency_precision': user_currency.decimal_places,
            'datas': datas,
            'start_date': start_date_str,
            'end_date': end_date_str,
        }

    @api.multi
    def _get_report_values(self, docids, data=None):
        data = dict(data or {})
        product_ids = self.env['product.product'].browse(data['product_ids'])
        data.update(self.get_report(data['start_date'], data['end_date'], product_ids))
        return data