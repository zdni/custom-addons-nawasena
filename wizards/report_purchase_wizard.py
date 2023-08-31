from odoo import fields, models, api, _
from odoo.exceptions import UserError
from datetime import datetime

import logging
_logger = logging.getLogger(__name__)

class ReportPurchaseWizard(models.TransientModel):
    _name = 'report.purchase.wizard'

    order_date = fields.Date('Order Date')
    order_ids = fields.Many2many('purchase.order', string='Purchase Order', required=True)

    @api.onchange('order_date')
    def _onchange_order_date(self):
        if self.order_date:
            early_day = self.order_date.strftime('%Y-%m-%d') + ' 00:00:00'
            end_of_day = self.order_date.strftime('%Y-%m-%d') + ' 23:59:59'
            early_day_obj = datetime.strptime(early_day, '%Y-%m-%d %H:%M:%S')
            end_of_day_obj = datetime.strptime(end_of_day, '%Y-%m-%d %H:%M:%S')

            orders = self.env['purchase.order'].search([ 
                ('date_order', '>=', early_day_obj), 
                ('date_order', '<=', end_of_day_obj),
            ])
            self.order_ids = orders.ids

            return {'domain': {'order_ids': [ ('id', 'in', orders.ids) ]}}
        else:
            self.order_ids = False
            return {'domain': {'order_ids': []}}

    @api.multi
    def print_excel(self):
        if len(self.order_ids) == 0:
            raise UserError(_('Select Purchase Order!'))
        
        data = {'ids': self.order_ids.ids, 'date': self.order_date.strftime('%d %b %Y')}
        return self.env.ref('custom_report_purchase.action_report_purchase_xlsx').report_action(self, data=data)
