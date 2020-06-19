# ?? 2018 Eficent (https://www.eficent.com)
# @author Jordi Ballester <jordi.ballester@eficent.com.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class res_company(models.Model):
    _inherit = 'res.company'

    no_negative_stock = fields.Boolean(string='No negative stock', default=True,
                                       help='Allows you to prohibit negative stock quantities.')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    no_negative_stock = fields.Boolean(related='company_id.no_negative_stock',
                                       string='不允许负库存', readonly=False,
                                       help='针对内部库位设置是否可以允许负库存')