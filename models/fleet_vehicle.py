from odoo import api, fields, models, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

class FleetVehicleLogFuel(models.Model):
    _inherit = 'fleet.vehicle.log.fuel'

    inv_adj_id = fields.Many2one('stock.inventory', string='Inventory Adjustment', readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
    ], string='State', default='draft')

    @api.onchange('liter')
    def _onchange_liter(self):
        if self.liter:
            product = self.env.user.company_id.product_usage_id
            if not product: raise UserError(_("Set Product Usage First!"))
            
            self.price_per_liter = product.standard_price

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state == 'posted':
                # reverse inventory adjustments
                product = self.env.user.company_id.product_usage_id
                if not product: raise UserError(_("Set Product Usage First!"))
                
                doc = self.env['stock.inventory'].create({
                    'name': 'Reverse Stok ' + str(product.name) + ' ' + str(rec.notes or ''),
                    'filter': 'product',
                    'product_id': product.id,
                    'reverse_doc_id': rec.inv_adj_id.id,
                })
                doc.action_start()
                
                for line in doc.line_ids:
                    if line.product_id.id == product.id:
                        line.product_qty = line.theoretical_qty + rec.liter
                doc.action_validate()

                date_obj = fields.Datetime.from_string( rec.date )
                for move in doc.move_ids:
                    move.write({ 'date': date_obj })

        return super(FleetVehicleLogFuel, self).unlink()
    
    @api.multi
    def action_posted(self):
        product = self.env.user.company_id.product_usage_id
        if not product: raise UserError(_("Set Product Usage First!"))
        
        for rec in self:
            doc = self.env['stock.inventory'].create({
                'name': 'Penggunaan ' + str(product.name) + " " + str(rec.notes or ''),
                'filter': 'product',
                'product_id': product.id
            })
            doc.action_start()
            
            for line in doc.line_ids:
                if line.product_id.id == product.id:
                    line.product_qty = line.theoretical_qty - rec.liter

            doc.action_validate()
            rec.write({'inv_adj_id': doc.id, 'state': 'posted'})

            date_obj = fields.Datetime.from_string(rec.date)
            for move in doc.move_ids:
                move.write({ 'date': date_obj })