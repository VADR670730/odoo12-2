# ?? 2015-2017 Akretion (http://www.akretion.com)
# @author Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api, _
from odoo.exceptions import ValidationError
from odoo.tools import config, float_compare


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    @api.multi
    @api.constrains('product_id', 'quantity')
    def check_negative_qty(self):
        p = self.env['decimal.precision'].precision_get(
            'Product Unit of Measure')

        for quant in self:
            location_id = quant.location_id
            flag = location_id.company_id.no_negative_stock and location_id.usage in ['internal', 'transit'] and float_compare(quant.quantity, 0, precision_digits=p) == -1
            if flag:
                lot_name = quant.lot_id.name_get()[0][1] if quant.lot_id else False
                owner_name = quant.owner_id.name_get()[0][1] if quant.owner_id else False
                msg = ""
                if lot_name and owner_name:
                    msg = _('不能执行该操作 \n库位： "%s" \n批次号： "%s" \n所有者： "%s" \n产品： "%s" \n库存量不足') % (quant.location_id.complete_name, lot_name, owner_name, quant.product_id.name)
                elif lot_name and not owner_name:
                    msg = _('不能执行该操作 \n库位： "%s" \n批次号： "%s" \n产品： "%s" \n库存量不足') % (quant.location_id.complete_name, lot_name, quant.product_id.name)
                elif not lot_name and owner_name:
                    msg = _('不能执行该操作 \n库位： "%s" \n所有者： "%s" \n产品： "%s" 库存量不足') % (quant.location_id.complete_name, owner_name, quant.product_id.name)
                elif not (lot_name or owner_name):
                    msg = _('不能执行该操作 \n库位： "%s" \n产品： "%s" \n库存量不足') % (quant.location_id.complete_name, quant.product_id.name)

                raise ValidationError(msg)
