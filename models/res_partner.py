from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = "res.partner"

    oat = fields.Monetary('OAT')
    mileage = fields.Float('Mileage (One-Way) (Km)')
    access_road_conditions = fields.Selection([
        ('bad', 'Rusak'),
        ('not_good', 'Kurang Bagus'),
        ('good', 'Bagus'),
    ], string='Access Road Conditions', default='good')
    solar_usage_ids = fields.One2many('solar.usage.delivery', 'customer_id', string='Detail', copy=False)

    @api.multi
    def write(self, vals):
        if vals.get('oat'):
            if self.property_product_pricelist: # object
                # update pricelist
                for item in self.property_product_pricelist.item_ids:
                    item.write({
                        'fixed_price': vals.get('oat')
                    })
            else:
                pricelist_temp_id = self.generate_pricelist_temp(vals.get('oat'), self.name)
                self.write({
                    'property_product_pricelist': pricelist_temp_id
                })

        return super(ResPartner, self).write(vals)
    
    @api.model
    def create(self, vals):
        if vals.get('customer'):
            if not vals.get('property_product_pricelist'):
                pricelist_temp_id = self.generate_pricelist_temp(vals.get('oat'), vals.get('name'))
                vals['property_product_pricelist'] = pricelist_temp_id

        result = super(ResPartner, self).create(vals)
        return result

    def generate_pricelist_temp(self, oat, customer_name):
        ProductPricelist = self.env['product.pricelist']
        ProductPricelistItem = self.env['product.pricelist.item']

        pricelist_temp = ProductPricelist.create({
            'name': 'Pricelist Delivery of ' + str(customer_name),
            'item_ids': False
        })

        products = self.env['setting.product.pricelist'].search([])
        # create item_ids
        for product in products:
            ProductPricelistItem.create({
                'applied_on': '1_product',
                'product_tmpl_id': product.product_id.id,
                'compute_price': 'fixed',
                'fixed_price': oat or 0.0,
                'pricelist_id': pricelist_temp.id,
                'is_delivery': True,
            })

        return pricelist_temp.id
    
class SolarUsageDelivery(models.Model):
    _name = 'solar.usage.delivery'
    _description = 'Solar Usage Delivery for Customer'

    def _default_currency_id(self):
        company_id = self.env.context.get('force_company') or self.env.context.get('company_id') or self.env.user.company_id.id
        return self.env['res.company'].browse(company_id).currency_id

    customer_id = fields.Many2one('res.partner', string='Customer', required=True, readonly=True)
    capacity_id = fields.Many2one('fleet.vehicle.tank.capacity', string='Tank Capacity (L)', required=True)
    solar_usage = fields.Float('Solar Usage (Round-Trip) (L)', required=True)
    fee = fields.Monetary('Fee Driver')

    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, readonly=True, default=lambda self: self.env.user.company_id.id)
    currency_id = fields.Many2one("res.currency", string="Currency", readonly=True, required=True, default=_default_currency_id)

