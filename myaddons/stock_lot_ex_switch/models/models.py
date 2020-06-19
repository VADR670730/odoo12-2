# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    module_stock_lot_ex = fields.Boolean("卸载stock_lot_ex模块",default=False)

    @api.onchange('module_stock_lot_ex')
    def _onchange_module_stock_lot_ex(self):
        self.module_procurement_jit = False
