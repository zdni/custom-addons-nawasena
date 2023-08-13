from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)

class SealNumberWizard(models.TransientModel):
    _name = 'seal.number.wizard'

    prefix = fields.Char('Prefix', required=True)
    start_number = fields.Integer('Start', required=True)
    end_number = fields.Integer('End', required=True)

    @api.multi
    def generate(self):
        length_code = len(str(self.end_number))

        for number in range(self.start_number, self.end_number+1):
            length = length_code - len(str(number))
            code = self.prefix + "0"*length + str(number)

            self.env['seal.number'].create({ 'name': code })
            
        return {'type': 'ir.actions.act_window_close'}