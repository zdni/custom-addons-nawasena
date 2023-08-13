from odoo import api, fields, models, tools, _

import logging
_logger = logging.getLogger(__name__)

class StockCardLine(models.Model):
    _name = 'stock.card.line'
    
    date			= fields.Datetime("Tanggal")
    description		= fields.Char("Deskripsi")
    information		= fields.Char("Deskripsi")
    loc_id          = fields.Many2one('stock.location', 'Lokasi', required=True)
    location_id		= fields.Many2one('stock.location', 'Lokasi Sumber', required=True)
    location_dest_id= fields.Many2one('stock.location', 'Lokasi Tujuan', required=True)
    picking_id		= fields.Many2one('stock.picking', 'Picking')
    product_id		= fields.Many2one('product.product', 'Produk', required=True)
    qty_start		= fields.Float("Qty Awal")
    qty_in			= fields.Float("Qty Masuk")
    qty_out			= fields.Float("Qty Keluar")
    qty_balance		= fields.Float("Qty Akhir")
    move_id         = fields.Many2one('stock.move', string='Move Ref')

    @api.model
    def process(self, product_id):
        product = self.env['product.product'].search([ ('id', '=', product_id) ])
        product_uom = product.uom_id

        moves = self.env['stock.move'].search([
            ('product_id.id', '=', product_id),
            ('has_count', '=', False),
            ('state', '=', 'done'),
        ], order='date ASC, id ASC')
        for move in moves:
            move.write({ 'has_count': True })
            information = ''                

            if move.location_id.usage == 'internal':
                loc_id = move.location_id.id
                description = "Barang Keluar dari " + move.location_id.location_id.name
                scl = self.env['stock.card.line'].search([
                    ('date', '<=', move.date),
                    ('product_id.id', '=', product_id),
                    ('description', 'in', ["Barang Keluar dari " + move.location_id.location_id.name, "Barang Masuk ke " + move.location_id.location_id.name])
                ], order="date desc, id desc", limit=1)
                qty_start = scl.qty_balance

                information = self.define_information(move)
                value = self.convert_uom( product_uom, move.product_uom, move.product_uom_qty )

                qty_out = value
                qty_in = 0
                qty_balance = qty_start + (qty_in -  qty_out)

                self.create_stock_card({ 
                    'product_id': product_id, 
                    'date': move.date, 
                    'information': information, 
                    'description': description, 
                    'loc_id': loc_id,
                    'location_id': move.location_id.id, 
                    'location_dest_id': move.location_dest_id.id,
                    'picking_id': move.picking_id.id,
                    'qty_start': qty_start,
                    'qty_in': qty_in,
                    'qty_out': qty_out,
                    'qty_balance': qty_balance,
                    'move_id': move.id,
                })

            if move.location_dest_id.usage == 'internal':
                loc_id = move.location_dest_id.id
                description = "Barang Masuk ke " + move.location_dest_id.location_id.name
                stock_card = self.env['stock.card.line'].search([
                    ('date', '<=', move.date),
                    ("product_id.id", "=", product_id),
                    ("description", "in", ["Barang Keluar dari " + move.location_dest_id.location_id.name, "Barang Masuk ke " + move.location_dest_id.location_id.name])
                ], order="date desc, id desc", limit=1)
                qty_start = stock_card.qty_balance

                information = self.define_information(move)
                value = self.convert_uom( product_uom, move.product_uom, move.product_uom_qty )

                qty_in = value
                qty_out = 0
                qty_balance = qty_start + (qty_in -  qty_out)
    
                self.create_stock_card({ 
                    'product_id': product_id, 
                    'date': move.date, 
                    'information': information, 
                    'description': description, 
                    'loc_id': loc_id,
                    'location_id': move.location_id.id, 
                    'location_dest_id': move.location_dest_id.id,
                    'picking_id': move.picking_id.id,
                    'qty_start': qty_start,
                    'qty_in': qty_in,
                    'qty_out': qty_out,
                    'qty_balance': qty_balance,
                    'move_id': move.id,
                })

    @api.model
    def create_stock_card(self, vals):
        res = super(StockCardLine, self).create(vals)
        return res

    def convert_uom(self, init, to, value):
        if to.uom_type == 'bigger':
            value = value*to.factor_inv
        if to.uom_type == 'smaller':
            value = value/to.factor
        
        if init.uom_type == 'bigger':
            value = value/init.factor_inv
        if init.uom_type == 'smaller':
            value = value*init.factor
        
        return value
    
    def define_information(self, move=False):
        information = ''
        if move.picking_id.name:
            if "WH/OUT" in move.picking_id.name:
                information = "Return Pembelian" if "Vendors" in move.picking_id.location_dest_id.name else "Penjualan"
            if "/IN/" in move.picking_id.name:
                information = "Return Penjualan" if "Customers" in move.picking_id.location_id.name  else "Pembelian"
            if "POS" in move.picking_id.name:
                information = "Penjualan Kasir"
            if "/OUT/" in move.picking_id.name:
                information = "Return Pembelian" if "Vendors" in move.picking_id.location_dest_id.name else "Penjualan"
            if "/INT/" in move.picking_id.name:
                information = "Transfer Item dari " + move.location_id.location_id.name + " ke " + move.location_dest_id.location_id.name
            if "RP" in move.picking_id.name:
                information = "Produksi"

            if move.move_remark: information = move.move_remark
        else:
            if move.location_dest_id.usage == 'inventory' or move.location_id.usage == 'inventory':
                information = move.reference

        return information