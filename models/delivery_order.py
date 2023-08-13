from odoo import api, fields, models, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

class TankHandover(models.Model):
    _name = 'tank.handover'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = 'Tank Handover'

    def name_get(self):
        res = []
        for rec in self:
            order_arr = []
            for order in rec.order_ids:
                order_arr.append(order.name)
            order_name = (', '.join(order_arr))
            res.append((rec.id, "(" + rec.name +  ") "  +order_name + " - " + rec.driver_id.name))
        
        return res
    
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        _logger.warning('_name_search')
        args = args or []
        if name:
            records = self.search(['|', '|', ('name', operator, name), ('driver_id.name', operator, name), ('order_ids', operator, name)])
            return records.name_get()
        return self.search([('name', operator, name)]+ args, limit=limit).name_get()
        
    @api.model
    def create(self, vals):
        handover_state_id = self.env.user.company_id.handover_state_id
        
        company_id = vals.get('company_id', self.default_get(['company_id'])['company_id'])
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].with_context(force_company=company_id).next_by_code('tank.handover') or '/'
        
        if 'vehicle_id' in vals:
            vehicle = self.env['fleet.vehicle'].search([ ('id', '=', vals['vehicle_id']) ])
            if vehicle and handover_state_id:
                vehicle.write({'state_id': handover_state_id.id})

        return super(TankHandover, self.with_context(company_id=company_id)).create(vals)

    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, readonly=True, default=lambda self: self.env.user.company_id.id)

    name = fields.Char('Name', required=True, copy=False, index=True, default=lambda self: _('New'))
    order_ids = fields.Many2many('sale.order', string='Order', domain=[('state', '=', 'sale')])
    driver_id = fields.Many2one('res.partner', string='Driver', domain=[('is_driver', '=', True)], required=True)
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle')
    fuel_id = fields.Many2one('fleet.vehicle.log.fuel', string='Fuel')
    delivery_date = fields.Date('Delivery Date', default=fields.Date.today(), required=True)
    is_fee = fields.Boolean('Fee', default=True)

    @api.onchange('driver_id')
    def _onchange_driver_id(self):
        if self.driver_id:
            vehicle = self.env['fleet.vehicle'].search([('driver_id.id', '=', self.driver_id.id)], limit=1)
            if vehicle: self.vehicle_id = vehicle.id

    @api.multi
    def unlink(self):
        for rec in self:
            handovers = self.env['delivery.driver'].search([ ('doc_ids', 'in', rec.id) ])
            
            if handovers: raise UserError(_("Can't Delete this Document because it has done a few tank handover!"))
            if rec.fuel_id: rec.fuel_id.unlink()
            
        return super(TankHandover, self).unlink()
    
    def action_view_handover_wizard(self):
        location = self.env.user.company_id.handover_location

        return {    
            'name': _("Tank Handover"),
            'type': 'ir.actions.act_window',
            'res_model': 'tank.handover.wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'context': { 
                'default_location': location, 
                'default_consignor_driver_id': self.driver_id.id,
                'default_order_id': self.order_ids[0].id if self.order_ids else False, #???
            }
        }
    
    def action_view_handover_doc(self):
        docs = self.env['delivery.driver'].search([('doc_ids', 'in', self.id)])
        action = self.env.ref('custom_delivery.action_delivery_driver').read()[0]
        if len(docs) > 0:
            action['domain'] = [('id', 'in', docs.ids)]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

class DeliveryDriver(models.Model):
    _name = 'delivery.driver'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = 'Delivery Driver'

    @api.model
    def create(self, vals):
        delivery_state_id = self.env.user.company_id.delivery_state_id

        company_id = vals.get('company_id', self.default_get(['company_id'])['company_id'])
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].with_context(force_company=company_id).next_by_code('delivery.driver') or '/'

        if 'vehicle_id' in vals:
            vehicle = self.env['fleet.vehicle'].search([ ('id', '=', vals['vehicle_id']) ])
            if vehicle and delivery_state_id:
                vehicle.write({'state_id': delivery_state_id.id})
                
        return super(DeliveryDriver, self.with_context(company_id=company_id)).create(vals)

    name = fields.Char('Name', required=True, copy=False, index=True, default=lambda self: _('New'))
    
    order_id = fields.Many2one('sale.order', string='Order')
    driver_id = fields.Many2one('res.partner', string='Driver', domain=[('is_driver', '=', True)], required=True)
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', required=True)
    fuel_id = fields.Many2one('fleet.vehicle.log.fuel', string='Fuel')
    delivery_date = fields.Date('Delivery Date', default=fields.Date.today(), required=True)
    end_date = fields.Date('Valid Until', default=fields.Date.today())

    # # handover
    doc_ids = fields.Many2many('tank.handover', string='Handover Reference')
    
    location = fields.Char('Location')

    change_vehicle_ids = fields.One2many('driver.change.vehicle', 'delivery_id', string='Change Vehicle')

    seal_number_ids = fields.One2many('delivery.seal.number', 'delivery_id', string='Seal Number')
    use_seal = fields.Boolean('Use Seal', default=False)
    
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, readonly=True, default=lambda self: self.env.user.company_id.id)

    @api.onchange('driver_id')
    def _onchange_driver_id(self):
        if self.driver_id:
            vehicle = self.env['fleet.vehicle'].search([('driver_id.id', '=', self.driver_id.id)], limit=1)
            if vehicle: self.vehicle_id = vehicle.id

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.fuel_id: rec.fuel_id.unlink()
            if rec.change_vehicle_ids:
                for line in rec.change_vehicle_ids:
                    line.unlink()

        return super(DeliveryDriver, self).unlink()

    # change vehicle
    def action_view_change_vehicle_wizard(self):
        return {    
            'name': _("Change Vehicle"),
            'type': 'ir.actions.act_window',
            'res_model': 'change.vehicle.wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
        }

    def action_view_change_vehicle(self):
        docs = self.env['driver.change.vehicle'].search([('delivery_id.id', '=', self.id)])
        action = self.env.ref('custom_delivery.action_driver_change_vehicle').read()[0]
        if len(docs) > 0:
            action['domain'] = [('id', 'in', docs.ids)]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action
    
    # action use seal number
    def use_seal_number(self):
        for line in self.seal_number_ids:
            for seal in line.seal_ids:
                seal.write({ 'is_used': True })

        self.write({ 'use_seal': True })
    
    def print_tank_handover(self):
        return self.env.ref('custom_delivery.action_report_tank_handover')\
            .with_context(discard_logo_check=True).report_action(self)

    def print_handover(self):
        return self.env.ref('custom_delivery.action_report_handover_delivery')\
            .with_context(discard_logo_check=True).report_action(self)

    @api.multi
    def print_travel_doc(self):
        return self.env.ref('custom_delivery.action_report_travel_doc')\
            .with_context(discard_logo_check=True).report_action(self)
        # return self.env.ref('custom_delivery.action_report_travel_doc_xlsx').report_action(self)

class DriverChangeVehicle(models.Model):
    _name = 'driver.change.vehicle'
    _description = 'Driver Change Vehicle'

    name = fields.Char('Descriptions', required=True)
    delivery_id = fields.Many2one('delivery.driver', string='Doc Reference', required=True)
    driver_id = fields.Many2one('res.partner', string='Driver', domain=[('is_driver', '=', True)])
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', required=True)
    
    seal_number_ids = fields.One2many('delivery.seal.number', 'change_vehicle_id', string='Seal Number')
    use_seal = fields.Boolean('Use Seal', default=False)
    
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, readonly=True, default=lambda self: self.env.user.company_id.id)

    @api.model
    def create(self, vals):
        delivery_state_id = self.env.user.company_id.delivery_state_id
        maintenance_state_id = self.env.user.company_id.maintenance_state_id
        
        company_id = vals.get('company_id', self.default_get(['company_id'])['company_id'])
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].with_context(force_company=company_id).next_by_code('driver.change.vehicle') or '/'
        
        if 'vehicle_id' in vals:
            vehicle = self.env['fleet.vehicle'].search([ ('id', '=', vals['vehicle_id']) ])
            if vehicle and delivery_state_id:
                vehicle.write({'state_id': delivery_state_id.id})
        
        if 'delivery_id' in vals:
            doc = self.env['delivery.driver'].search([ ('id', '=', vals['delivery_id']) ])
            if doc.vehicle_id and maintenance_state_id:
                doc.vehicle_id.write({'state_id': maintenance_state_id.id})

        return super(DriverChangeVehicle, self.with_context(company_id=company_id)).create(vals)
    
    # action use seal number
    def use_seal_number(self):
        for line in self.seal_number_ids:
            for seal in line.seal_ids:
                seal.write({ 'is_used': True })

        self.write({ 'use_seal': True })

    def recalculate_solar_usage(self):
        if self.delivery_id.fuel_id:
            self.delivery_id.fuel_id.write({ 'vehicle_id': self.vehicle_id.id })

class DeliverySealNumber(models.Model):
    _name = 'delivery.seal.number'
    _description = 'Delivery Seal Number'

    seal_ids = fields.Many2many('seal.number', string='Seal', required=True)
    position = fields.Selection([
        ('top', 'Top'),
        ('bottom', 'Bottom'),
    ], string='Position', default='top', required=True)
    delivery_id = fields.Many2one('delivery.driver', string='Doc Reference')
    change_vehicle_id = fields.Many2one('driver.change.vehicle', string='Doc Reference')
    
class HandoverConditions(models.Model):
    _name = 'handover.conditions'
    _order = 'sequence asc'

    name = fields.Char('Name', required=True)
    sequence = fields.Integer(help="Used to order the note stages")