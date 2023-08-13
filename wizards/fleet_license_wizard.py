from odoo import fields, models, api, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

class FleetLicenseWizard(models.TransientModel):
    _name = 'fleet.license.wizard'

    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')

    @api.onchange('start_date')
    def _onchange_start_date(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            self.end_date = self.start_date

    @api.onchange('end_date')
    def _onchange_end_date(self):
        if self.end_date and self.end_date < self.start_date:
            self.start_date = self.end_date

    @api.multi
    def generate_report(self):
        if (not self.env.user.company_id.logo):
            raise UserError(_("You have to set a logo or a layout for your company."))
        elif (not self.env.user.company_id.external_report_layout_id):
            raise UserError(_("You have to set your reports's header and footer layout."))
        data = {'date_start': self.start_date, 'date_stop': self.end_date}
        return self.env.ref('custom_fleet.fleet_license_report').report_action([], data=data)