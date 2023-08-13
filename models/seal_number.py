from odoo import api, fields, models, _
from odoo.exceptions import UserError

class SealNumber(models.Model):
    _name = 'seal.number'
    _description = 'Seal Number'

    name = fields.Char('Seal Number', required=True)
    is_used = fields.Boolean('Is Used', default=False, readonly=True)

    @api.multi
    def unlink(self):
        for doc in self:
            if doc.is_used:
                raise UserError(_("Can't delete seal number that has been used!"))
        return super(SealNumber, self).unlink()