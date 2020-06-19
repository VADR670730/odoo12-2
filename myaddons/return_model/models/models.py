# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp
from odoo.tools import float_is_zero, float_compare
from odoo.exceptions import UserError


class ReturnOrder(models.Model):
    _name = "return.order"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    READONLY_STATES = {
        'picking': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
        'invoice': [('readonly', True)],
    }

    name = fields.Char(string='Order Reference', required=True, copy=False, readonly=True, states={'draft': [('readonly', False)]}, index=True, default=lambda self: _('New'))
    state = fields.Selection([
        ('draft', '草稿'),
        ('picking', '调拨中'),
        ('invoice', '可开发票中'),
        ('done', '完成'),
        ('cancel', '取消'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3, default='draft')
    user_id = fields.Many2one('res.users', string='Salesperson', index=True, track_visibility='onchange', track_sequence=2, default=lambda self: self.env.user)
    group_id = fields.Many2one('procurement.group', string="Procurement Group", copy=False)
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, change_default=True, index=True, track_visibility='always', track_sequence=1)
    partner_invoice_id = fields.Many2one('res.partner', string='Invoice Address',  required=True)
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account', readonly=True, copy=False, oldname='project_id')
    order_line = fields.One2many('return.order.line', 'order_id', string='Order Lines', copy=True, auto_join=True)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env['res.company']._company_default_get('return.order'))
    sale_orders = fields.Many2many('sale.order',string = "对应的销售订单")
    fiscal_position_id = fields.Many2one('account.fiscal.position', oldname='fiscal_position', string='Fiscal Position')
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist', required=True, readonly=True, states={'draft': [('readonly', False)]}, help="Pricelist for current sales order.")
    currency_id = fields.Many2one("res.currency", related='pricelist_id.currency_id', string="Currency", readonly=True,required=True)
    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, compute='_amount_all', track_visibility='onchange', track_sequence=5)
    amount_tax = fields.Monetary(string='Taxes', store=True, readonly=True, compute='_amount_all')
    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all', track_visibility='always', track_sequence=6)
    date_order = fields.Datetime('Order Date', required=True, states=READONLY_STATES, index=True, copy=False, default=fields.Datetime.now,
                                 help="Depicts the date where the Quotation should be validated and converted into a purchase order.")
    invoice_count = fields.Integer(compute="_compute_invoice", string='Bill Count', copy=False, default=0, store=True)
    invoice_ids = fields.Many2many('account.invoice', compute="_compute_invoice", string='Bills', copy=False, store=True)
    invoice_status = fields.Selection([
        ('no', 'Nothing to Bill'),
        ('to invoice', 'Waiting Bills'),
        ('invoiced', 'No Bill to Receive'),
    ], string='Billing Status', compute='_get_invoiced', store=True, readonly=True, copy=False, default='no')
    picking_count = fields.Integer(compute='_compute_picking', string='Picking count', default=0, store=True)
    picking_ids = fields.Many2many('stock.picking', compute='_compute_picking', string='Receptions', copy=False, store=True)
    dest_address_id = fields.Many2one('res.partner', string='Drop Ship Address', states=READONLY_STATES,
        help="Put an address if you want to deliver directly from the vendor to the customer. ""Otherwise, keep empty to deliver to your own company.")

    # selected_lines = fields.Many2many('sale.order.line',string='选择的退货明细行')
    selected_lines = fields.Many2many('sale.order.line',string='选择的退货明细行',compute='_get_selected_lines')

    @api.depends('order_line.select_order_line')
    def _get_selected_lines(self):
        new = self.order_line.mapped('select_order_line')
        self.selected_lines = new

    @api.model
    def _default_picking_type(self):
        type_obj = self.env['stock.picking.type']
        company_id = self.env.context.get('company_id') or self.env.user.company_id.id
        types = type_obj.search([('code', '=', 'incoming'), ('warehouse_id.company_id', '=', company_id)])
        if not types:
            types = type_obj.search([('code', '=', 'incoming'), ('warehouse_id', '=', False)])
        return types[:1]
    picking_type_id = fields.Many2one('stock.picking.type', 'Deliver To', states=READONLY_STATES, required=True, default=_default_picking_type,
        help="This will determine operation type of incoming shipment")

    # @api.multi
    # def action_view_invoice(self):
    #     # invoices = self.mapped('invoice_ids')
    #     result = self.env.ref('account.action_invoice_out_refund').read()[0]
    #     create_bill = self.env.context.get('create_bill', False)
    #
    #     result['context'] = {
    #         'default_purchase_id': self.id,
    #         'default_currency_id': self.currency_id.id,
    #         'default_company_id': self.company_id.id,
    #         'company_id': self.company_id.id
    #     }
    #     # choose the view_mode accordingly
    #     if len(self.invoice_ids) > 1 and not create_bill:
    #         result['domain'] = "[('id', 'in', " + str(self.invoice_ids.ids) + ")]"
    #     else:
    #         res = self.env.ref('account.invoice_supplier_form', False)
    #         result['views'] = [(res and res.id or False, 'form')]
    #         # Do not set an invoice_id if we want to create a new bill.
    #         if not create_bill:
    #             result['res_id'] = self.invoice_ids.id or False
    #     return result



        # if len(invoices) > 1:
        #     action['domain'] = [('id', 'in', invoices.ids)]
        # elif len(invoices) == 1:
        #     action['views'] = [(self.env.ref('account.invoice_form').id, 'form')]
        #     action['res_id'] = invoices.ids[0]
        # else:
        #     action = {'type': 'ir.actions.act_window_close'}
        # return action
        #

    @api.multi
    def _get_destination_location(self):
        self.ensure_one()
        if self.dest_address_id:
            return self.dest_address_id.property_stock_customer.id
        return self.picking_type_id.default_location_dest_id.id

    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        inv_obj = self.env['account.invoice']
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        invoices = {}
        references = {}
        invoices_origin = {}
        invoices_name = {}

        for order in self:
            group_key = order.id if grouped else (order.partner_invoice_id.id, order.currency_id.id)

            # We only want to create sections that have at least one invoiceable line
            for line in order.order_line:
                if group_key not in invoices:
                    inv_data = order._prepare_invoice()
                    invoice = inv_obj.create(inv_data)
                    references[invoice] = order
                    invoices[group_key] = invoice
                    invoices_origin[group_key] = [invoice.origin]
                    invoices_name[group_key] = [invoice.name]

                elif group_key in invoices:
                    if order.name not in invoices_origin[group_key]:
                        invoices_origin[group_key].append(order.name)
                    # if order.client_order_ref and order.client_order_ref not in invoices_name[group_key]:
                    #     invoices_name[group_key].append(order.client_order_ref)

                if line.qty_to_invoice > 0:
                    line.invoice_line_create(invoices[group_key].id, line.qty_to_invoice)

            if references.get(invoices.get(group_key)):
                if order not in references[invoices[group_key]]:
                    references[invoices[group_key]] |= order

        for group_key in invoices:
            invoices[group_key].write({'name': ', '.join(invoices_name[group_key]),
                                       'origin': ', '.join(invoices_origin[group_key])})

            sale_orders = references[invoices[group_key]]
            if len(sale_orders) == 1:
                invoices[group_key].reference = sale_orders.name

        if not invoices:
            raise UserError(_('There is no invoiceable line. If a product has a Delivered quantities invoicing policy, please make sure that a quantity has been delivered.'))

        for invoice in invoices.values():
            invoice.compute_taxes()
            if not invoice.invoice_line_ids:
                raise UserError(_('There is no invoiceable line. If a product has a Delivered quantities invoicing policy, please make sure that a quantity has been delivered.'))
            # If invoice is negative, do a refund invoice instead
            if invoice.amount_total < 0:
                invoice.type = 'out_refund'
                for line in invoice.invoice_line_ids:
                    line.quantity = -line.quantity
            # Use additional field helper function (for account extensions)
            for line in invoice.invoice_line_ids:
                line._set_additional_fields(invoice)
            # Necessary to force computation of taxes. In account_invoice, they are triggered
            # by onchanges, which are not triggered when doing a create.
            invoice.compute_taxes()
            # Idem for partner
            so_payment_term_id = invoice.payment_term_id.id
            invoice._onchange_partner_id()
            # To keep the payment terms set on the SO
            invoice.payment_term_id = so_payment_term_id
            invoice.message_post_with_view('mail.message_origin_link',
                values={'self': invoice, 'origin': references[invoice]},
                subtype_id=self.env.ref('mail.mt_note').id)
        return [inv.id for inv in invoices.values()]

    '''
    @api.multi
    def _prepare_invoice(self):

        self.ensure_one()
        journal_id = self.env['account.invoice'].default_get(['journal_id'])['journal_id']
        if not journal_id:
            raise UserError(_('Please define an accounting sales journal for this company.'))
        invoice_vals = {
            'name': self.client_order_ref or '',
            'origin': self.name,
            'type': 'out_refund',
            'account_id': self.partner_invoice_id.property_account_receivable_id.id,
            'partner_id': self.partner_invoice_id.id,
            'partner_shipping_id': self.partner_shipping_id.id,
            'journal_id': journal_id,
            'currency_id': self.pricelist_id.currency_id.id,
            'comment': self.note,
            'payment_term_id': self.payment_term_id.id,
            'fiscal_position_id': self.fiscal_position_id.id or self.partner_invoice_id.property_account_position_id.id,
            'company_id': self.company_id.id,
            'user_id': self.user_id and self.user_id.id,
            'team_id': self.team_id.id,
            'transaction_ids': [(6, 0, self.transaction_ids.ids)],
        }
        return invoice_vals
    '''

    @api.multi
    def action_view_invoice(self):
        invoices = self.mapped('invoice_ids')
        action = self.env.ref('account.action_invoice_tree1').read()[0]
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            action['views'] = [(self.env.ref('account.invoice_form').id, 'form')]
            action['res_id'] = invoices.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    @api.multi
    def _prepare_invoice(self):
        self.ensure_one()
        journal_id = self.env['account.invoice'].default_get(['journal_id'])['journal_id']
        if not journal_id:
            raise UserError(_('Please define an accounting sales journal for this company.'))
        invoice_vals = {
            'name': '',
            'origin': self.name,
            'type': 'out_refund',
            'account_id': self.partner_invoice_id.property_account_receivable_id.id,
            'partner_id': self.partner_invoice_id.id,
            'partner_shipping_id': self.partner_invoice_id.id,
            'journal_id': journal_id,
            'currency_id': self.pricelist_id.currency_id.id,
            'fiscal_position_id': self.fiscal_position_id.id or self.partner_invoice_id.property_account_position_id.id,
            'company_id': self.company_id.id,
            'user_id': self.user_id and self.user_id.id,
        }
        return invoice_vals

    @api.multi
    def button_confirm(self):
        for order in self:
            if order.state not in ['draft',]:
                continue
            self._create_picking()
            self.write({'state': 'picking'})

        return True

    @api.depends('order_line.move_ids.returned_move_ids',
                 'order_line.move_ids.state',
                 'order_line.move_ids.picking_id')
    def _compute_picking(self):
        for order in self:
            pickings = self.env['stock.picking']
            for line in order.order_line:
                # We keep a limited scope on purpose. Ideally, we should also use move_orig_ids and
                # do some recursive search, but that could be prohibitive if not done correctly.
                moves = line.move_ids | line.move_ids.mapped('returned_move_ids')
                pickings |= moves.mapped('picking_id')
            order.picking_ids = pickings
            order.picking_count = len(pickings)

    @api.model
    def _prepare_picking(self):
        if not self.group_id:
            self.group_id = self.group_id.create({
                'name': self.name,
                'partner_id': self.partner_id.id
            })
        return {
            'picking_type_id': self.picking_type_id.id,
            'partner_id': self.partner_id.id,
            'date': self.date_order,
            'origin': self.name,
            'location_dest_id': self._get_destination_location(),
            'location_id': self.partner_id.property_stock_supplier.id or self.partner_id.property_stock_customer.id,
            'company_id': self.company_id.id,
        }

    @api.multi
    def _create_picking(self):
        StockPicking = self.env['stock.picking']
        for order in self:
            if any([ptype in ['product', 'consu'] for ptype in order.order_line.mapped('product_id.type')]):
                pickings = order.picking_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
                if not pickings:
                    res = order._prepare_picking()
                    picking = StockPicking.create(res)
                else:
                    picking = pickings[0]
                moves = order.order_line._create_stock_moves(picking)
                moves = moves.filtered(lambda x: x.state not in ('done', 'cancel'))._action_confirm()
                seq = 0
                for move in sorted(moves, key=lambda move: move.date_expected):
                    seq += 5
                    move.sequence = seq
                moves._action_assign()
                picking.message_post_with_view('mail.message_origin_link',
                    values={'self': picking, 'origin': order},
                    subtype_id=self.env.ref('mail.mt_note').id)
        return True

    @api.depends('order_line.invoice_lines.invoice_id')
    def _compute_invoice(self):
        for order in self:
            invoices = self.env['account.invoice']
            for line in order.order_line:
                invoices |= line.invoice_lines.mapped('invoice_id')
            order.invoice_ids = invoices
            order.invoice_count = len(invoices)

    @api.depends('state', 'order_line.qty_invoiced', 'order_line.qty_received', 'order_line.product_qty')
    def _get_invoiced(self):
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for order in self:
            if order.state not in ['picking','done']:
                order.invoice_status = 'no'
                continue
            if any(float_compare(line.qty_invoiced, line.qty_received, precision_digits=precision) == -1 for line in order.order_line):
                order.invoice_status = 'to invoice'
            elif all(float_compare(line.qty_invoiced, line.qty_received, precision_digits=precision) >= 0 for line in order.order_line) and order.invoice_ids:
                order.invoice_status = 'invoiced'
            else:
                order.invoice_status = 'no'

    @api.depends('order_line.price_total')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
            order.update({
                'amount_untaxed': order.pricelist_id.currency_id.round(amount_untaxed),
                'amount_tax': order.pricelist_id.currency_id.round(amount_tax),
                'amount_total': amount_untaxed + amount_tax,
            })

    @api.multi
    def action_view_picking(self):
        """ This function returns an action that display existing picking orders of given purchase order ids. When only one found, show the picking immediately.
        """
        action = self.env.ref('stock.action_picking_tree_all')
        result = action.read()[0]
        # override the context to get rid of the default filtering on operation type
        result['context'] = {}
        pick_ids = self.mapped('picking_ids')
        # choose the view_mode accordingly
        if not pick_ids or len(pick_ids) > 1:
            result['domain'] = "[('id','in',%s)]" % (pick_ids.ids)
        elif len(pick_ids) == 1:
            res = self.env.ref('stock.view_picking_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = pick_ids.id
        return result

    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if not self.partner_id:
            self.update({
                'partner_invoice_id': False,
            })
            return

        addr = self.partner_id.address_get(['delivery', 'invoice'])
        values = {
            'pricelist_id': self.partner_id.property_product_pricelist and self.partner_id.property_product_pricelist.id or False,
            'partner_invoice_id': addr['invoice'],
            'user_id': self.partner_id.user_id.id or self.env.uid
        }
        self.update(values)

    # @api.onchange('sale_orders')
    # def get_order_line(self):
    #
    #     order_line_ids = set(self.order_line.mapped("sale_order_id").ids)
    #     if False in order_line_ids:
    #         order_line_ids.remove(False)
    #     sale_orders = self.sale_orders
    #     sale_orders_ids = set(sale_orders.mapped('id'))
    #
    #     to_sale_orders_ids = sale_orders_ids - order_line_ids
    #
    #     sale_order_lines = self.env['sale.order.line'].search([['order_id','in',list(to_sale_orders_ids)]]) if to_sale_orders_ids else []
    #
    #     if len(sale_orders_ids) < len(order_line_ids):
    #         to_remove_line = self.env['return.order.line']
    #         for return_line in self.order_line:
    #             id = return_line.sale_order_id.id
    #             if id and id not in sale_orders_ids:
    #                 to_remove_line |= return_line
    #         self.order_line = self.order_line - to_remove_line
    #
    #     for line in sale_order_lines:
    #         value = line.read(fields=["product_id","product_uom_qty","price_unit"])[0]
    #         value.pop('id')
    #         value['sale_order_id'] = line.order_id.id
    #         value['product_qty'] = value.pop('product_uom_qty',0)
    #         value['name'] = line.product_id.name
    #         new_return_line = self.env['return.order.line'].new(values=value)
    #         new_return_line.tax_id = line.tax_id
    #         new_return_line.product_uom = line.product_uom
    #         self.order_line = self.order_line | new_return_line


    # @api.onchange('order_line')
    # def onchange_order_line(self):
    #
    #     order_line_ids = set(self.order_line.mapped("sale_order_id").ids)
    #     if False in order_line_ids:
    #         order_line_ids.remove(False)
    #
    #     sale_orders = self.sale_orders
    #     sale_orders_ids = set(sale_orders.mapped('id'))
    #
    #     if len(sale_orders_ids) > len(order_line_ids):
    #         to_remove_sale_order = self.env['sale.order']
    #         for sale_order in self.sale_orders:
    #             id = sale_order.id
    #             if id and id not in order_line_ids:
    #                 to_remove_sale_order |= sale_order
    #         self.sale_orders = self.sale_orders - to_remove_sale_order

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('return.order') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('return.order') or _('New')
        result = super().create(vals)
        return result


class ReturnOrderLine(models.Model):

    _name = "return.order.line"

    order_id = fields.Many2one("return.order", string="Order Reference",ondelete='cascade', index=True)
    invoice_lines = fields.Many2many('account.invoice.line', 'return_order_line_invoice_rel', 'order_line_id', 'invoice_line_id', string='Invoice Lines', copy=False)
    name = fields.Text(string='Description')
    price_unit = fields.Float(string='Unit Price', required=True, digits=dp.get_precision('Product Price'), default=0.0)
    price_subtotal = fields.Monetary(string='Subtotal',compute='_compute_amount',  readonly=True, store=True)
    price_tax = fields.Float(string='Total Tax', compute='_compute_amount',readonly=True, store=True)
    price_total = fields.Monetary(compute='_compute_amount', string='Total', readonly=True, store=True)
    product_id = fields.Many2one('product.product', string='Product', change_default=True, ondelete='restrict',required=True)
    product_uom_qty = fields.Float(string='Total Quantity', compute='_compute_product_uom_qty', store=True)
    product_qty = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'), required=True)
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure')
    tax_id = fields.Many2many('account.tax', string='Taxes', domain=['|', ('active', '=', False), ('active', '=', True)])
    discount = fields.Float(string='Discount (%)', digits=dp.get_precision('Discount'), default=0.0)
    company_id = fields.Many2one(related='order_id.company_id', string='Company', store=True, readonly=True)
    currency_id = fields.Many2one(related='order_id.currency_id', depends=['order_id'], store=True, string='Currency', readonly=True)
    sale_order_id = fields.Many2one('sale.order', string='所属销售订单')
    sale_order_name = fields.Char(string='所属销售订单编号',readonly=True, related='sale_order_id.name')
    qty_invoiced = fields.Float(compute='_compute_qty_invoiced', string="Billed Qty", digits=dp.get_precision('Product Unit of Measure'), store=True)
    qty_received = fields.Float(string="Received Qty", digits=dp.get_precision('Product Unit of Measure'), copy=False)
    date_order = fields.Datetime(related='order_id.date_order', string='Order Date', readonly=True)
    state = fields.Selection(related='order_id.state', string='Order Status', readonly=True, copy=False, store=True, default='draft')
    move_ids = fields.One2many('stock.move', 'return_line_id', string='Reservation', readonly=True, ondelete='set null', copy=False)
    qty_to_invoice = fields.Float(compute='_get_to_invoice_qty', string='To Invoice Quantity', store=True, readonly=True,digits=dp.get_precision('Product Unit of Measure'))
    # move_line_id = fields.One2many("stock.move.line", "return_line_id", string='Reservation', readonly=True, ondelete='set null', copy=False)

    select_order_line = fields.Many2one("sale.order.line",string="销售订单明细行")

    @api.onchange("select_order_line")
    def _get_return_line(self):
        select_order_line = self.select_order_line
        if select_order_line:
            self.sale_order_id = select_order_line.order_id.id
            self.product_qty = select_order_line.product_uom_qty
            self.name = select_order_line.product_id.name
            self.product_id = select_order_line.product_id
            self.price_unit = select_order_line.price_unit
            self.tax_id = select_order_line.tax_id
            self.product_uom = select_order_line.product_uom

    @api.depends('qty_invoiced', 'qty_received', 'product_qty', 'order_id.state')
    def _get_to_invoice_qty(self):
        for line in self:
            if line.order_id.state not in ['cancel','draft']:
                if line.product_id.invoice_policy == 'order':
                    line.qty_to_invoice = line.product_qty - line.qty_invoiced
                else:
                    line.qty_to_invoice = line.qty_received - line.qty_invoiced
            else:
                line.qty_to_invoice = 0

    @api.multi
    @api.depends('product_uom', 'product_qty', 'product_id.uom_id')
    def _compute_product_uom_qty(self):
        for line in self:
            if line.product_id.uom_id != line.product_uom:
                line.product_uom_qty = line.product_uom._compute_quantity(line.product_qty, line.product_id.uom_id)
            else:
                line.product_uom_qty = line.product_qty

    @api.depends('invoice_lines.invoice_id.state', 'invoice_lines.quantity')
    def _compute_qty_invoiced(self):
        for line in self:
            qty = 0.0
            for inv_line in line.invoice_lines:
                if inv_line.invoice_id.state not in ['cancel']:
                    if inv_line.invoice_id.type == 'out_refund':
                        qty += inv_line.uom_id._compute_quantity(inv_line.quantity, line.product_uom)
                    # if inv_line.invoice_id.type == 'in_invoice':
                    #     qty += inv_line.uom_id._compute_quantity(inv_line.quantity, line.product_uom)
                    # elif inv_line.invoice_id.type == 'in_refund':
                    #     qty -= inv_line.uom_id._compute_quantity(inv_line.quantity, line.product_uom)
            line.qty_invoiced = qty

    @api.depends('product_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_qty, product=line.product_id, partner=line.order_id.partner_invoice_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    @api.onchange('product_uom', 'product_qty')
    def product_uom_change(self):
        if not self.product_uom or not self.product_id:
            self.price_unit = 0.0
            return
        if self.order_id.pricelist_id and self.order_id.partner_id:
            product = self.product_id.with_context(
                lang=self.order_id.partner_id.lang,
                partner=self.order_id.partner_id,
                quantity=self.product_qty,
                date=self.order_id.date_order,
                pricelist=self.order_id.pricelist_id.id,
                uom=self.product_uom.id,
                fiscal_position=self.env.context.get('fiscal_position')
            )
            self.price_unit = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        if not self.product_id:
            # return {'domain': {'product_uom': []}}
            return
        vals = {}
        domain = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        if not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id):
            vals['product_uom'] = self.product_id.uom_id
            vals['product_qty'] = self.product_qty or 1.0

        product = self.product_id.with_context(
            lang=self.order_id.partner_id.lang,
            partner=self.order_id.partner_id,
            quantity=vals.get('product_qty') or self.product_qty,
            date=self.order_id.date_order,
            pricelist=self.order_id.pricelist_id.id,
            uom=self.product_uom.id
        )

        result = {'domain': domain}

        title = False
        message = False
        warning = {}
        if product.sale_line_warn != 'no-message':
            title = _("Warning for %s") % product.name
            message = product.sale_line_warn_msg
            warning['title'] = title
            warning['message'] = message
            result = {'warning': warning}
            if product.sale_line_warn == 'block':
                self.product_id = False
                return result
        self._compute_tax_id()

        if self.order_id.pricelist_id and self.order_id.partner_id:
            vals['price_unit'] = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)
        self.update(vals)

        return result


    @api.multi
    def _compute_tax_id(self):
        for line in self:
            fpos = line.order_id.fiscal_position_id or line.order_id.partner_id.property_account_position_id
            # If company_id is set, always filter taxes by the company
            taxes = line.product_id.taxes_id.filtered(lambda r: not line.company_id or r.company_id == line.company_id)
            line.tax_id = fpos.map_tax(taxes, line.product_id, line.order_id.partner_invoice_id) if fpos else taxes

    @api.multi
    def _get_display_price(self, product):

        if self.order_id.pricelist_id.discount_policy == 'with_discount':
            return product.with_context(pricelist=self.order_id.pricelist_id.id).price
        product_context = dict(self.env.context, partner_id=self.order_id.partner_id.id, date=self.order_id.date_order, uom=self.product_uom.id)

        final_price, rule_id = self.order_id.pricelist_id.with_context(product_context).get_product_price_rule(self.product_id, self.product_qty or 1.0, self.order_id.partner_id)
        base_price, currency = self.with_context(product_context)._get_real_price_currency(product, rule_id, self.product_qty, self.product_uom, self.order_id.pricelist_id.id)
        if currency != self.order_id.pricelist_id.currency_id:
            base_price = currency._convert(
                base_price, self.order_id.pricelist_id.currency_id,
                self.order_id.company_id, self.order_id.date_order or fields.Date.today())
        # negative discounts (= surcharge) are included in the display price
        return max(base_price, final_price)

    @api.multi
    def _prepare_stock_moves(self, picking):
        self.ensure_one()
        res = []
        if self.product_id.type not in ['product', 'consu']:
            return res
        qty = 0.0
        price_unit = self.price_unit
        for move in self.move_ids.filtered(lambda x: x.state != 'cancel' and not x.location_dest_id.usage == "supplier"):
            qty += move.product_uom._compute_quantity(move.product_qty, self.product_uom, rounding_method='HALF-UP')
        template = {
            'name': self.name or '',
            'product_id': self.product_id.id,
            'product_uom': self.product_uom.id,
            'date': self.order_id.date_order,
            'location_id': self.order_id.partner_id.property_stock_supplier.id or self.order_id.partner_id.property_stock_customer.id,
            'location_dest_id': self.order_id._get_destination_location(),
            'picking_id': picking.id,
            'partner_id': self.order_id.dest_address_id.id,
            'state': 'draft',
            'return_line_id': self.id,
            'company_id': self.order_id.company_id.id,
            'price_unit': price_unit,
            'picking_type_id': self.order_id.picking_type_id.id,
            'group_id': self.order_id.group_id.id,
            'origin': self.order_id.name,
            'route_ids': self.order_id.picking_type_id.warehouse_id and [(6, 0, [x.id for x in self.order_id.picking_type_id.warehouse_id.route_ids])] or [],
            'warehouse_id': self.order_id.picking_type_id.warehouse_id.id,
        }
        diff_quantity = self.product_qty - qty
        if float_compare(diff_quantity, 0.0,  precision_rounding=self.product_uom.rounding) > 0:
            quant_uom = self.product_id.uom_id
            get_param = self.env['ir.config_parameter'].sudo().get_param
            if self.product_uom.id != quant_uom.id and get_param('stock.propagate_uom') != '1':
                product_qty = self.product_uom._compute_quantity(diff_quantity, quant_uom, rounding_method='HALF-UP')
                template['product_uom'] = quant_uom.id
                template['product_uom_qty'] = product_qty
            else:
                template['product_uom_qty'] = diff_quantity
            res.append(template)
        return res

    @api.multi
    def _create_stock_moves(self, picking):
        moves = self.env['stock.move']
        done = self.env['stock.move'].browse()
        for line in self:
            for val in line._prepare_stock_moves(picking):
                done += moves.create(val)
        return done


    def _update_received_qty(self):
        line_count = len(self)
        total = 0.0
        if line_count == 1:
            for move in self.move_ids:
                if move.state == 'done':
                    total += move.product_uom._compute_quantity(move.product_uom_qty, self.product_uom)

        return_order_lines = self.order_id.order_line
        if line_count != len(return_order_lines):
            for line in return_order_lines:
                line.qty_received = line.product_qty if line.product_qty < total else total
                total -= line.product_qty
                total = 0 if total <= 0 else total

        if line_count == len(return_order_lines):
            for line in self:
                total = 0.0
                for move in line.move_ids:
                    if move.state == 'done':
                        total += move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom)
                line.qty_received = total


    @api.multi
    def _prepare_invoice_line(self, qty):
        """
        Prepare the dict of values to create the new invoice line for a sales order line.

        :param qty: float quantity to invoice
        """
        self.ensure_one()
        res = {}
        account = self.product_id.property_account_income_id or self.product_id.categ_id.property_account_income_categ_id

        if not account and self.product_id:
            raise UserError(_('Please define income account for this product: "%s" (id:%d) - or for its category: "%s".') %
                (self.product_id.name, self.product_id.id, self.product_id.categ_id.name))

        fpos = self.order_id.fiscal_position_id or self.order_id.partner_id.property_account_position_id
        if fpos and account:
            account = fpos.map_account(account)

        res = {
            'name': "return",
            'origin': self.order_id.name,
            'account_id': account.id,
            'price_unit': self.price_unit,
            'quantity': qty,
            'discount': self.discount,
            'uom_id': self.product_uom.id,
            'product_id': self.product_id.id or False,
            'invoice_line_tax_ids': [(6, 0, self.tax_id.ids)],
            'account_analytic_id': self.order_id.analytic_account_id.id,
        }
        return res

    @api.multi
    def invoice_line_create(self, invoice_id, qty):

        invoice_lines = self.env['account.invoice.line']
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for line in self:
            if not float_is_zero(qty, precision_digits=precision) or not line.product_id:
                vals = line._prepare_invoice_line(qty=qty)
                vals.update({'invoice_id': invoice_id, 'return_line_ids': [(6, 0, [line.id])]})
                invoice_lines |= self.env['account.invoice.line'].create(vals)
        return invoice_lines

    @api.onchange('product_id')
    def _onchange_product_id_uom_check_availability(self):
        if not self.product_uom or (self.product_id.uom_id.category_id.id != self.product_uom.category_id.id):
            self.product_uom = self.product_id.uom_id

    @api.multi
    def write(self, values):
        result = super(ReturnOrderLine, self).write(values)
        # Update expected date of corresponding moves
        if 'product_qty' in values:
            self.filtered(lambda l: l.order_id.state == 'picking')._create_or_update_picking()
        return result

    @api.model
    def create(self, values):
        line = super(ReturnOrderLine, self).create(values)
        if line.order_id.state == 'picking':
            line._create_or_update_picking()
        return line

    @api.multi
    def _create_or_update_picking(self):
        for line in self:
            if line.product_id.type in ('product', 'consu'):
                # Prevent decreasing below received quantity
                if float_compare(line.product_qty, line.qty_received, line.product_uom.rounding) < 0:
                    raise UserError(_('You cannot decrease the ordered quantity below the received quantity.\n'
                                      'Create a return first.'))

                # if float_compare(line.product_qty, line.qty_invoiced, line.product_uom.rounding) == -1:
                #     # If the quantity is now below the invoiced quantity, create an activity on the vendor bill
                #     # inviting the user to create a refund.
                #     activity = self.env['mail.activity'].sudo().create({
                #         'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                #         'note': _('The quantities on your purchase order indicate less than billed. You should ask for a refund. '),
                #         'res_id': line.invoice_lines[0].invoice_id.id,
                #         'res_model_id': self.env.ref('account.model_account_invoice').id,
                #     })
                #     activity._onchange_activity_type_id()

                # If the user increased quantity of existing line or created a new line
                pickings = line.order_id.picking_ids.filtered(lambda x: x.state not in ('done', 'cancel') and x.location_dest_id.usage in ('internal', 'transit'))
                picking = pickings and pickings[0] or False
                if not picking:
                    res = line.order_id._prepare_picking()
                    picking = self.env['stock.picking'].create(res)
                move_vals = line._prepare_stock_moves(picking)
                for move_val in move_vals:
                    self.env['stock.move']\
                        .create(move_val)\
                        ._action_confirm()\
                        ._action_assign()


class SaleOrder(models.Model):
    _inherit = "sale.order"

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.multi
    def onchange(self, values, field_name, field_onchange):
        print(self)
        return super().onchange(values,field_name,field_onchange)

# class ProductTemplate(models.Model):
#     _inherit = "product.template"
#     multi_specification_pro_ = fields.Many2one('product.template', string = "多规格产品M2O")
#     multi_specification_pro = fields.One2many('product.template','multi_specification_pro_',string='多规格产品', help='当前产品对应的多个规格的产品')
#     flag_multi = fields.Boolean(string='是否多规格',default=False)


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    return_line_ids = fields.Many2many(
        'return.order.line',
        'return_order_line_invoice_rel',
        'invoice_line_id', 'order_line_id',
        string='Return Order Lines', readonly=True, copy=False)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    return_id = fields.Many2one('return.order', related='move_lines.return_line_id.order_id',
        string="Purchase Orders", readonly=True)


class StockMove(models.Model):
    _inherit = 'stock.move'

    return_line_id = fields.Many2one('return.order.line',
        'Return Order Line', ondelete='set null', index=True, readonly=True)

    def _action_done(self):
        res = super(StockMove, self)._action_done()
        # self.mapped('move_line_ids').mapped("return_line_id")._update_received_qty()
        self.mapped("return_line_id")._update_received_qty()
        return res


# class StockMoveLine(models.Model):
#     _inherit = "stock.move.line"
#
#     return_line_id = fields.Many2one('return.order.line',
#         'Return Order Line', ondelete='set null', index=True, readonly=True)