from dateutil.relativedelta import relativedelta
from datetime import timedelta
from odoo import api, fields, models

import logging

_logger = logging.getLogger(__name__)


class StockRule(models.Model):
    _inherit = 'stock.rule'

    # 实现交货单传值
    def _get_stock_move_values(self, product_id, product_qty, product_uom, location_id, name, origin, values, group_id):

        ''' Returns a dictionary of values that will be used to create a stock move from a procurement.
        This function assumes that the given procurement has a rule (action == 'pull' or 'pull_push') set on it.

        :param procurement: browse record
        :rtype: dictionary
        '''
        date_expected = fields.Datetime.to_string(
            fields.Datetime.from_string(values['date_planned']) - relativedelta(days=self.delay or 0)
        )
        # it is possible that we've already got some move done, so check for the done qty and create
        # a new move with the correct qty
        qty_left = product_qty
        move_values = {
            'name': name[:2000],
            'company_id': self.company_id.id or self.location_src_id.company_id.id or self.location_id.company_id.id or
                          values['company_id'].id,
            'product_id': product_id.id,
            'product_uom': product_uom.id,
            'product_uom_qty': qty_left,
            'partner_id': self.partner_address_id.id or (
                    values.get('group_id', False) and values['group_id'].partner_id.id) or False,
            'location_id': self.location_src_id.id,
            'location_dest_id': location_id.id,
            'move_dest_ids': values.get('move_dest_ids', False) and [(4, x.id) for x in values['move_dest_ids']] or [],
            'rule_id': self.id,
            'procure_method': self.procure_method,
            'origin': origin,
            'picking_type_id': self.picking_type_id.id,
            'group_id': group_id,
            'route_ids': [(4, route.id) for route in values.get('route_ids', [])],
            'warehouse_id': self.propagate_warehouse_id.id or self.warehouse_id.id,
            'date': date_expected,
            'date_expected': date_expected,
            'propagate': self.propagate,
            'priority': values.get('priority', "1"),
            'product_unit': values.get('product_sale_unit'),
            # 'product_sale_num': values.get('product_sale_num'),

        }
        for field in self._get_custom_move_fields():
            if field in values:
                move_values[field] = values.get(field)
        return move_values


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # 实现交货单传值
    @api.multi
    def _prepare_procurement_values(self, group_id=False):
        """ Prepare specific key for moves or other components that will be created from a stock rule
        comming from a sale order line. This method could be override in order to add other custom key that could
        be used in move/po creation.
        """
        values = super(SaleOrderLine, self)._prepare_procurement_values(group_id)
        self.ensure_one()
        date_planned = self.order_id.confirmation_date \
                       + timedelta(days=self.customer_lead or 0.0) - timedelta(
            days=self.order_id.company_id.security_lead)
        values.update({
            'company_id': self.order_id.company_id,
            'group_id': group_id,
            'sale_line_id': self.id,
            'date_planned': date_planned,
            'route_ids': self.route_id,
            'warehouse_id': self.order_id.warehouse_id or False,
            'partner_id': self.order_id.partner_shipping_id.id,
            # 'product_sale_num': self.product_sale_num,
            'product_sale_unit': self.product_sale_unit.id,

        })
        for line in self.filtered("order_id.commitment_date"):
            date_planned = fields.Datetime.from_string(line.order_id.commitment_date) - timedelta(
                days=line.order_id.company_id.security_lead)
            values.update({
                'date_planned': fields.Datetime.to_string(date_planned),
            })
        return values
