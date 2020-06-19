# -*- coding: utf-8 -*-

from . import controllers
from . import models
from odoo import api, SUPERUSER_ID


def pre_init_hook(cr):
    env = api.Environment(cr, SUPERUSER_ID, {})

    module_ids = env['ir.module.module'].search([('name', '=', "procurement_jit"),("state","=","installed")])
    module_ids.sudo().module_uninstall()
