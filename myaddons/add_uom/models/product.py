from itertools import chain

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_compare, float_is_zero, float_round


class Pricelist(models.Model):
    _inherit = "product.pricelist"

    pricelist_move_id = fields.Char(string='明细行选择')

# 给订单明细行选择价格时添加计量单位约束
    @api.multi
    def _compute_price_rule(self, products_qty_partner, date=False, uom_id=False):
        """ Low-level method - Mono pricelist, multi products
        Returns: dict{product_id: (price, suitable_rule) for the given pricelist}

        If date in context: Date of the pricelist (%Y-%m-%d)

            :param products_qty_partner: list of typles products, quantity, partner
            :param datetime date: validity date
            :param ID uom_id: intermediate unit of measure
        """
        # print(products_qty_partner)
        self.ensure_one()
        if not date:
            date = self._context.get('date') or fields.Date.context_today(self)
        if not uom_id and self._context.get('uom'):
            uom_id = self._context['uom']
        if uom_id:
            # rebrowse with uom if given
            products = [item[0].with_context(uom=uom_id) for item in products_qty_partner]

            products_qty_partner = [(products[index], data_struct[1], data_struct[2]) for index, data_struct in
                                    enumerate(products_qty_partner)]

        else:
            products = [item[0] for item in products_qty_partner]

        if not products:
            return {}

        categ_ids = {}
        for p in products:
            categ = p.categ_id
            while categ:
                categ_ids[categ.id] = True
                categ = categ.parent_id
        categ_ids = list(categ_ids)

        is_product_template = products[0]._name == "product.template"
        if is_product_template:
            prod_tmpl_ids = [tmpl.id for tmpl in products]
            # all variants of all products
            prod_ids = [p.id for p in
                        list(chain.from_iterable([t.product_variant_ids for t in products]))]
        else:
            prod_ids = [product.id for product in products]
            prod_tmpl_ids = [product.product_tmpl_id.id for product in products]

        # Load all rules
        self._cr.execute(
            'SELECT item.id '
            'FROM product_pricelist_item AS item '
            'LEFT JOIN product_category AS categ '
            'ON item.categ_id = categ.id '
            'WHERE (item.product_tmpl_id IS NULL OR item.product_tmpl_id = any(%s))'
            'AND (item.product_id IS NULL OR item.product_id = any(%s))'
            'AND (item.categ_id IS NULL OR item.categ_id = any(%s)) '
            'AND (item.pricelist_id = %s) '
            'AND (item.date_start IS NULL OR item.date_start<=%s) '
            'AND (item.date_end IS NULL OR item.date_end>=%s)'
            'ORDER BY item.applied_on, item.min_quantity desc, categ.complete_name desc, item.id desc',
            (prod_tmpl_ids, prod_ids, categ_ids, self.id, date, date))
        # NOTE: if you change `order by` on that query, make sure it matches
        # _order from model to avoid inconstencies and undeterministic issues.

        sale_uoms = self._context.get('sale_uom')

        item_ids = [x[0] for x in self._cr.fetchall()]
        # print(item_ids,'item_ids')
        items = self.env['product.pricelist.item'].browse(item_ids)
        # print(items, 'items')
        results = {}
        for product, qty, partner in products_qty_partner:
            # print(len(products_qty_partner),6354)
            results[product.id] = 0.0
            suitable_rule = False

            # Final unit price is computed according to `qty` in the `qty_uom_id` UoM.
            # An intermediary unit price may be computed according to a different UoM, in
            # which case the price_uom_id contains that UoM.
            # The final price will be converted to match `qty_uom_id`.
            qty_uom_id = self._context.get('uom') or product.uom_id.id
            price_uom_id = product.uom_id.id
            qty_in_product_uom = qty
            if qty_uom_id != product.uom_id.id:
                try:
                    qty_in_product_uom = self.env['uom.uom'].browse([self._context['uom']])._compute_quantity(qty,
                                                                                                              product.uom_id)
                except UserError:
                    # Ignored - incompatible UoM in context, use default product UoM
                    pass

            # if Public user try to access standard price from website sale, need to call price_compute.
            # TDE SURPRISE: product can actually be a template
            price = product.price_compute('list_price')[product.id]

            price_uom = self.env['uom.uom'].browse([qty_uom_id])

            # sale_context = self.env['sale.order.line'].context_get()
            # print(sale_context,'sale_context')

            for rule in items:
                # print(rule.product_sale_uom,'rl')
                # print(sale_uoms, 'sale_uoms')
                if rule.product_measuring_unit_name == sale_uoms:
                    # print(rule.product_sale_uom, '单位相等')
                    if rule.min_quantity and qty_in_product_uom < rule.min_quantity:
                        continue
                    if is_product_template:
                        if rule.product_tmpl_id and product.id != rule.product_tmpl_id.id:
                            continue
                        if rule.product_id and not (
                                product.product_variant_count == 1 and product.product_variant_id.id == rule.product_id.id):
                            # product rule acceptable on template if has only one variant
                            continue
                    else:
                        if rule.product_tmpl_id and product.product_tmpl_id.id != rule.product_tmpl_id.id:
                            continue
                        if rule.product_id and product.id != rule.product_id.id:
                            continue
                if rule.product_measuring_unit_name == sale_uoms:
                    if rule.categ_id:
                        cat = product.categ_id
                        while cat:
                            if cat.id == rule.categ_id.id:
                                break
                            cat = cat.parent_id
                        if not cat:
                            continue
                if rule.product_measuring_unit_name == sale_uoms:
                    if rule.base == 'pricelist' and rule.base_pricelist_id:
                        price_tmp = rule.base_pricelist_id._compute_price_rule([(product, qty, partner)])[product.id][
                            0]  # TDE: 0 = price, 1 = rule
                        price = rule.base_pricelist_id.currency_id._convert(price_tmp, self.currency_id,
                                                                            self.env.user.company_id, date, round=False)
                    else:
                        # if base option is public price take sale price else cost price of product
                        # price_compute returns the price in the context UoM, i.e. qty_uom_id
                        price = product.price_compute(rule.base)[product.id]

                convert_to_price_uom = (lambda price: product.uom_id._compute_price(price, price_uom))
                # print(convert_to_price_uom,'convert_to_price_uom')

                if rule.product_measuring_unit_name == sale_uoms:
                    if price is not False:
                        if rule.compute_price == 'fixed':
                            price = convert_to_price_uom(rule.fixed_price)
                        elif rule.compute_price == 'percentage':
                            price = (price - (price * (rule.percent_price / 100))) or 0.0
                        else:
                            # complete formula
                            price_limit = price
                            price = (price - (price * (rule.price_discount / 100))) or 0.0
                            if rule.price_round:
                                price = tools.float_round(price, precision_rounding=rule.price_round)

                            if rule.price_surcharge:
                                price_surcharge = convert_to_price_uom(rule.price_surcharge)
                                price += price_surcharge

                            if rule.price_min_margin:
                                price_min_margin = convert_to_price_uom(rule.price_min_margin)
                                price = max(price, price_limit + price_min_margin)

                            if rule.price_max_margin:
                                price_max_margin = convert_to_price_uom(rule.price_max_margin)
                                price = min(price, price_limit + price_max_margin)
                        suitable_rule = rule
                    break
            # Final price conversion into pricelist currency
            if suitable_rule and suitable_rule.compute_price != 'fixed' and suitable_rule.base != 'pricelist':
                price = product.currency_id._convert(price, self.currency_id, self.env.user.company_id, date,
                                                     round=False)
            results[product.id] = (price, suitable_rule and suitable_rule.id or False)

        return results


class StockingPicking(models.Model):
    _inherit = 'stock.picking'

# 判断所输入完成数量与所选择的计量单位是否符合
    @api.multi
    def button_validate(self):
        self.ensure_one()
        if not self.move_lines and not self.move_line_ids:
            raise UserError(_('Please add some items to move.'))

        # If no lots when needed, raise error
        picking_type = self.picking_type_id
        precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        no_quantities_done = all(
            float_is_zero(move_line.qty_done, precision_digits=precision_digits) for move_line in self.move_line_ids)
        no_reserved_quantities = all(
            float_is_zero(move_line.product_qty, precision_rounding=move_line.product_uom_id.rounding) for move_line in
            self.move_line_ids)
        if no_reserved_quantities and no_quantities_done:
            raise UserError(_(
                'You cannot validate a transfer if no quantites are reserved nor done. To force the transfer, switch in edit more and encode the done quantities.'))

        for line in self.move_ids_without_package:
            if line.quantity_done == 0:
                break
            print(line.quantity_done)
            # uom_env = self.env['uom.uom'].search([('name', '=', line.product_unit)])
            if line.product_unit.factor_inv == 0:
                break

            result = line.quantity_done / line.product_unit.factor_inv
            print(result, 'result')
            result1 = int(result)
            if result != result1:
                raise ValidationError('您输入的完成数量与所选择的销售单位不符')


        if picking_type.use_create_lots or picking_type.use_existing_lots:
            lines_to_check = self.move_line_ids
            if not no_quantities_done:
                lines_to_check = lines_to_check.filtered(
                    lambda line: float_compare(line.qty_done, 0,
                                               precision_rounding=line.product_uom_id.rounding)
                )

            for line in lines_to_check:
                product = line.product_id
                if product and product.tracking != 'none':
                    if not line.lot_name and not line.lot_id:
                        raise UserError(
                            _('You need to supply a Lot/Serial number for product %s.') % product.display_name)

        if no_quantities_done:
            view = self.env.ref('stock.view_immediate_transfer')
            wiz = self.env['stock.immediate.transfer'].create({'pick_ids': [(4, self.id)]})
            return {
                'name': _('Immediate Transfer?'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'stock.immediate.transfer',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'res_id': wiz.id,
                'context': self.env.context,
            }

        if self._get_overprocessed_stock_moves() and not self._context.get('skip_overprocessed_check'):
            view = self.env.ref('stock.view_overprocessed_transfer')
            wiz = self.env['stock.overprocessed.transfer'].create({'picking_id': self.id})
            return {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'stock.overprocessed.transfer',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'res_id': wiz.id,
                'context': self.env.context,
            }

        # Check backorder should check for other barcodes
        if self._check_backorder():
            return self.action_generate_backorder_wizard()
        self.action_done()
        return
