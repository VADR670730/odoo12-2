# -*- coding: utf-8 -*-
from odoo import models, fields, api
import re


class ResCompany(models.Model):
    _inherit = "res.company"

    ems_type = fields.Boolean(string=u'有无账册类型')
    ems_no = fields.Char(string=u'金二账册编号')


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    rlt_no = fields.Char(string=u'关联单证编号')

    @api.onchange('rlt_no')
    def check_no(self):
        if self.rlt_no:
            string = re.sub('[\，]', ',', self.rlt_no)
            self.rlt_no = string.replace(' ', '')


class SaleOrder(models.Model):
    _inherit = "sale.order"

    rlt_no = fields.Char(string=u'关联单证编号')
    expected_date = fields.Datetime("Expected Date", store=True)
    expected_date = fields.Datetime("Expected Date", compute='_compute_expected_date', store=True,
                                    oldname='commitment_date',  # Note: can not be stored since depends on today()
                                    help="Delivery date you can promise to the customer, computed from product lead times and from the shipping policy of the order.")

    @api.onchange('rlt_no')
    def check_no(self):
        if self.rlt_no:
            string = re.sub('[\，]', ',', self.rlt_no)
            self.rlt_no = string.replace(' ', '')


class StockPicking(models.Model):
    _inherit = "stock.picking"

    logistics_no = fields.Char(string=u'物流运单编号')
    logistics_cd = fields.Char(string=u'物流企业代码')
    logistics_nm_id = fields.Many2one('res.partner', string=u'物流企业名称')
    handlingin_id = fields.Char(string=u'入仓单号')

    warehouse_cd1 = fields.Char(string=u'仓库代码1', compute='_onchange_warehouse1', store=True)
    warehouse_cd = fields.Char(string=u'仓库代码', compute='_onchange_warehouse', store=True)

    picking_t = fields.Char(string='picking_t', compute='_compute_location', store=True)
    picking_t1 = fields.Char(string='picking_t1', compute='_compute_out_location', store=True)

    p_rlt_no = fields.Char(string=u'收货关联单证编号', compute='compute_location_p', store=True)
    s_rlt_no = fields.Char(string=u'交货关联单证编号', compute='compute_location_s', store=True)

    @api.one
    @api.depends('origin')
    def compute_location_p(self):
        if self.origin:
            obj = self.env['purchase.order'].search([('origin', '=', self.origin)], limit=1)
            self.p_rlt_no = obj.rlt_no

    @api.one
    @api.depends('origin')
    def compute_location_s(self):
        if self.origin:
            obj = self.env['sale.order'].search([('origin', '=', self.origin)], limit=1)
            self.s_rlt_no = obj.rlt_no

    @api.onchange('handlingin_id')
    def check_no(self):
        if self.handlingin_id:
            string = re.sub('[\，]', ',', self.handlingin_id)
            self.handlingin_id = string.replace(' ', '')

    @api.one
    @api.depends('picking_type_id')
    def _onchange_warehouse1(self):
        if self.location_dest_id:
            self.warehouse_cd1 = self.location_dest_id.location_id.name

    @api.one
    @api.depends('picking_type_id')
    def _onchange_warehouse(self):
        if self.location_id:
            self.warehouse_cd = self.location_id.location_id.name
            # print("onchange", self.location_id.location_id.name, self.location_id.name)

    @api.one
    @api.depends('picking_type_id')
    def _compute_location(self):
        picking_type_obj = self.env['stock.picking.type'].search([('name', '=', '交货单')])
        picking_type_obj1 = self.env['stock.picking.type'].search([('name', '=', 'Delivery Orders')])
        num = picking_type_obj.ids
        num1 = picking_type_obj1.ids
        for i in num1:
            num.append(i)
        self.picking_t = 0
        if self.picking_type_id:
            if self.picking_type_id.id in num:
                self.picking_t = 1

    @api.one
    @api.depends('picking_type_id')
    def _compute_out_location(self):
        picking_type_obj = self.env['stock.picking.type'].search([('name', '=', '收货')])
        picking_type_obj1 = self.env['stock.picking.type'].search([('name', '=', 'Receipts')])
        num = picking_type_obj.ids
        num1 = picking_type_obj1.ids
        for i in num1:
            num.append(i)
        self.picking_t1 = 0
        if self.picking_type_id:
            if self.picking_type_id.id in num:
                self.picking_t1 = 1

    @api.model
    def create(self, vals):
        # TDE FIXME: clean that brol
        defaults = self.default_get(['name', 'picking_type_id'])
        if vals.get('name', '/') == '/' and defaults.get('name', '/') == '/' and vals.get('picking_type_id', defaults.get('picking_type_id')):
            vals['name'] = self.env['stock.picking.type'].browse(vals.get('picking_type_id', defaults.get('picking_type_id'))).sequence_id.next_by_id()

        # TDE FIXME: what ?
        # As the on_change in one2many list is WIP, we will overwrite the locations on the stock moves here
        # As it is a create the format will be a list of (0, 0, dict)
        if vals.get('move_lines') and vals.get('location_id') and vals.get('location_dest_id'):
            for move in vals['move_lines']:
                if len(move) == 3 and move[0] == 0:
                    move[2]['location_id'] = vals['location_id']
                    move[2]['location_dest_id'] = vals['location_dest_id']
        res = super(StockPicking, self).create(vals)
        res._autoconfirm_picking()

        if res.logistics_nm_id or res.logistics_nm_id or res.logistics_cd:
            delivery_obj = self.env['delivery.table'].create({
                    'logistics_nm': res.logistics_nm_id.name,
                    'logistics_cd': res.logistics_cd,
                    'handlingout_id': res.name,
                    'origin_stock_picking': res.id,
                    'enterp_nm': res.company_id.name,
                    'enterp_cd': res.company_id.vat
            })
            pro_list = []
            flag2 = 0
            for i in res.move_ids_without_package:
                flag = str(i.product_id.name) + "/" + str(i.quantity_done) + "/" + str(i.product_uom.name)
                flag2 += i.quantity_done
                pro_list.append(flag)
            delivery_obj.update({
                'goods_info': pro_list,
                'pack_no': flag2
            })
            res.logistics_no = delivery_obj.logistics_no
        return res


class ProductTemplate(models.Model):
    _inherit = "product.template"

    gds_seqno = fields.Float(string=u'项号')
    gds_mtno = fields.Char(string=u'备案商品料号')
    code_ts = fields.Char(string=u'备案商品编码')
    gds_name = fields.Char(string='备案商品名称')
    gds_model = fields.Char(string=u'备案规格型号')
    natcd = fields.Char(string=u'原产地')
    g_unit_id = fields.Many2one('uom.uom', string=u'备案计量单位')
    g_unit_ratio = fields.Float(string=u'企业内部计量单位与备案计量单位换算比例')
    unit_1_id = fields.Many2one('uom.uom', string=u'第一计量单位')
    unit_1_ratio = fields.Float(string=u'企业内部计量单位与第一计量单位换算比例')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env['res.company']._company_default_get('product.template'), index=1, store=True)
    currency_id = fields.Selection([('AUD', 'AUD'),
                                    ('CNY', 'CNY'),
                                    ('EUR', 'EUR'),
                                    ('GBP', 'GBP'),
                                    ('HKD', 'HKD'),
                                    ('JPY', 'JPY'),
                                    ('KRW', 'KRW'),
                                    ('TWD', 'TWD'),
                                    ('USD', 'USD'),], string=u'币种')


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    warehouse_type = fields.Selection([(u'有账册保税', u'有账册保税'), (u'无账册保税', u'无账册保税'), (u'非保税', u'非保税')], string=u'库位标识')
    warehouse_property = fields.Selection([(u'库存区', u'库存区'), (u'其他区', u'其他区')], string=u'库位属性')
    product_uom_id = fields.Many2one(
        'uom.uom', 'Unit of Measure',
        readonly=True, related='product_id.uom_id', store=True)
    warehouse_cd = fields.Char(string=u'仓库代码', compute='compute_location', store=True)
    companys_id = fields.Many2one('res.company', string='Company', store=True, default=lambda self: self.env.user.company_id)
    # company_id = fields.Many2one('res.company', string='Company', store=True, readonly=True, default=lambda self: self.env.user.company_id.id)

    @api.one
    @api.depends('location_id')
    def compute_location(self):
        if self.location_id:
            self.warehouse_cd = self.location_id.location_id.name


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    move_num = fields.Char(string=u'货物移动流水号', store=True)
    in_rack_date = fields.Datetime(string=u'目标库位上架时间', compute='_compute_date', store=True)
    out_rack_date = fields.Datetime(string=u'源库位下架时间', compute='_compute_date', store=True)
    companys_id = fields.Many2one('res.company', string='Companys', store=True,
                                  default=lambda self: self.env.user.company_id)

    @api.one
    @api.depends('date')
    def _compute_date(self):
        if self.date:
            self.in_rack_date = self.date
            self.out_rack_date = self.date


class ResCompany(models.Model):
    _inherit = "res.company"

    vat = fields.Char(related='partner_id.vat', string="Tax ID", readonly=False, store=True)
