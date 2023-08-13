import logging
from datetime import timedelta

import pytz

from odoo import fields, models, api, _

_logger = logging.getLogger(__name__)

class ReportFleetLicense(models.AbstractModel):
    _name = 'report.custom_fleet.report_fleet_license'

    @api.model
    def generate_report(self, date_start=False, date_stop=False):
        user_currency = self.env.user.company_id.currency_id

        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        today = user_tz.localize(fields.Datetime.from_string(fields.Date.context_today(self)))
        today = today.astimezone(pytz.timezone('UTC'))
        if date_start:
            date_start = fields.Datetime.from_string(date_start)
        else:
            date_start = today

        if date_stop:
            date_stop = fields.Datetime.from_string(date_stop)
        else:
            date_stop = today + timedelta(days=1, seconds=-1)
         
        date_stop = max(date_stop, date_start)

        date_start = fields.Datetime.to_string(date_start)
        date_stop = fields.Datetime.to_string(date_stop)

        datas = {}

        legals = self.env['fleet.vehicle.license.list'].search([
            ('expiry_date', '>=', date_start),
            ('expiry_date', '<=', date_stop),
        ], order='vehicle_id ASC, expiry_date ASC')

        for legal in legals:
            data = {
                'license': legal.license_id.name,
                'number': legal.number,
                'registration_date': legal.registration_date,
                'expiry_date': legal.expiry_date,
                'state': legal.status_id.name,
            }
            
            if legal.vehicle_id.name in datas:
                datas[legal.vehicle_id.name].append(data)
            else:
                datas[legal.vehicle_id.name] = [data]


        return {
            'currency_precision': user_currency.decimal_places,
            'datas': datas
        }

    @api.multi
    def _get_report_values(self, docids, data=None):
        data = dict(data or {})
        data.update(self.generate_report(data['date_start'], data['date_stop']))
        return data