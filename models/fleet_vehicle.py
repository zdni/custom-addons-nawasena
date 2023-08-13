from odoo import api, fields, models, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

class FleetVehicleLogFuel(models.Model):
    _inherit = 'fleet.vehicle.log.fuel'

    purchaser_id = fields.Many2one('res.partner', 'Purchaser', domain="[('is_driver','=',True)]")

class FleetVehicle(models.Model):
    _inherit = "fleet.vehicle"

    capacity_id = fields.Many2one('fleet.vehicle.tank.capacity', string='Tank Capacity (L)')

    gauge_tank_log_ids = fields.One2many('fleet.gauge.tank.log', 'vehicle_id', string='Gauge Tank Logs', copy=False)
    license_ids = fields.One2many('fleet.vehicle.license.list', 'vehicle_id', string='License', copy=False)
    equipment_ids = fields.One2many('fleet.vehicle.equipment.list', 'vehicle_id', string='Equipment', copy=False)

    @api.onchange('driver_id')
    def _onchange_driver_id(self):
        if self.driver_id:
            vehicle = self.env['fleet.vehicle'].search([ ('driver_id.id', '=', self.driver_id.id) ])
            if vehicle: raise UserError(_("Driver can't have multiple vehicle!"))

class FleetVehicleTankCapacity(models.Model):
    _name = 'fleet.vehicle.tank.capacity'

    name = fields.Integer('Tank Capacity (L)', required=True)

class FleetGaugeTankLog(models.Model):
    _name = "fleet.gauge.tank.log"

    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', required=True, ondelete='cascade', index=True, copy=False)
    value = fields.Float('Value', required=True)
    expiry_date = fields.Date('Expiry Date')

class FleeLicense(models.Model):
    _name = "fleet.license"

    name = fields.Char('Name', required=True)
    short_name = fields.Char('Short Name', required=True)

class FleeLicenseStatus(models.Model):
    _name = "fleet.license.status"
    _order = 'sequence asc'

    name = fields.Char('Name', required=True)
    sequence = fields.Integer(help="Used to order the note stages")
    
    _sql_constraints = [('fleet_license_state_name_unique', 'unique(name)', 'State name already exists')]

class FleetVehicleLicenseList(models.Model):
    _name = "fleet.vehicle.license.list"

    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', required=True, ondelete='cascade', index=True, copy=False)
    license_id = fields.Many2one('fleet.license', string='License', required=True)
    number = fields.Char('Number', required=True)
    registration_date = fields.Date('Registration Date', required=True)
    expiry_date = fields.Date('Expiry Date')
    status_id = fields.Many2one('fleet.license.status', string='Status', required=True)

class FleetVehicleEquipmentList(models.Model):
    _name = "fleet.vehicle.equipment.list"

    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', required=True, ondelete='cascade', index=True, copy=False)
    equipment_id = fields.Many2one('product.product', string='Equipment', domain="[('is_equipment', '=', True)]", required=True)
    qty = fields.Integer('Qty', required=True)
    description = fields.Char('Description')

class FleetServiceType(models.Model):
    _inherit = 'fleet.service.type'

    product_id = fields.Many2one('product.product', string='Product', domain="[('type', '=', 'product')]")

class FleetVehicleCost(models.Model):
    _inherit = 'fleet.vehicle.cost'

    @api.depends('cost_subtype_id', 'qty', 'unit_price')
    def _compute_amount(self):
        for doc in self:
            if doc.cost_subtype_id and doc.qty and doc.unit_price:
                doc.update({ 'amount': doc.unit_price*doc.qty })

    @api.onchange('cost_subtype_id')
    def _onchange_cost_subtype_id(self):
        if self.cost_subtype_id:
            product_price = self.cost_subtype_id.product_id and self.cost_subtype_id.product_id.standard_price or 0
            self.unit_price = product_price

    amount = fields.Float('Total Price', compute="_compute_amount", store=True)
    qty = fields.Float('Qty', default="1")
    unit_price = fields.Float('Unit Price', default="1")

class FleetVehicleLogServices(models.Model):
    _inherit = 'fleet.vehicle.log.services'
    
    @api.depends('cost_ids')
    def _compute_amount(self):
        for doc in self:
            if doc.cost_ids:
                amount = 0
                for line in doc.cost_ids:
                    amount += line.amount
                
                doc.update({ 'amount': amount })

    amount = fields.Float('Total Price', compute="_compute_amount", store=True)
    purchaser_id = fields.Many2one('res.partner', 'Purchaser', domain="[('is_driver','=',True)]")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
    ], string='State', default='draft')
    type = fields.Selection([
        ('workshop', 'Workshop'),
        ('external', 'External'),
    ], string='Type', default='workshop', required=True)

    inv_adj_id = fields.Many2one('stock.inventory', string='Inventory Adjustment', readonly=True)

    @api.multi
    def action_posted(self):
        for rec in self:
            inv_adj_id = False
            if self.type == 'workshop':
                doc = self.env['stock.inventory'].create({
                    'name': 'Service Log ' + str(self.vehicle_id.name or ''),
                    'filter': 'partial',
                })
                doc.action_start()

                for line in rec.cost_ids:
                    if line.cost_subtype_id.product_id:
                        product = line.cost_subtype_id.product_id
                        theoretical_qty = product.get_theoretical_quantity(
                            product.id,
                            doc.location_id.id,
                            to_uom=product.uom_id.id,
                        )
                        if theoretical_qty-line.qty < 0: raise UserError(_("Can't Progress this Log because some products don't have enough qty!"))
                        
                        self.env['stock.inventory.line'].create({
                            'inventory_id': doc.id,
                            'product_id': product.id,
                            'product_uom_id': product.uom_id.id,
                            'theoretical_qty': theoretical_qty,
                            'product_qty': theoretical_qty-line.qty,
                            'location_id': doc.location_id.id,
                        })

                doc.action_validate()

                date_obj = fields.Datetime.from_string(rec.date)
                for move in doc.move_ids:
                    move.write({ 'date': date_obj })
                
                inv_adj_id = doc.id

            rec.write({ 'state': 'posted', 'inv_adj_id': inv_adj_id })
