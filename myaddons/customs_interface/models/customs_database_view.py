# -*- coding: utf-8 -*-
from odoo import tools
from odoo import api, fields, models


class PurchaseDatabaseView(models.Model):
    _name = "purchase.database.view"
    _auto = False

    company_vat = fields.Char(string=u'税号')
    partner_vat = fields.Char(string=u'供应商编码')
    company_id = fields.Many2one('res.company', string='Company')
    name = fields.Text(string='Description', required=True)
    create_date = fields.Datetime(string='create_date')
    partner_id = fields.Many2one('res.partner', string='Partner')
    default_code = fields.Char('Internal Reference', index=True)
    product_id = fields.Many2one('product.product', string='Product')
    product_qty = fields.Float(string='Quantity')
    product_uom = fields.Many2one('uom.uom', string='Product Unit of Measure')
    price_total = fields.Monetary(string='Total')
    currency_id = fields.Many2one(string='Currency')
    date_order = fields.Datetime(string='单据日期')
    write_date = fields.Datetime(string=u'最后更新日期')

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'purchase_database_view')
        self.env.cr.execute("""
           CREATE OR REPLACE VIEW purchase_database_view AS
           (SELECT
                r.vat as company_vat,
                e.vat as partner_vat,
                r.name as company_id,
                s.name as name,
                e.name as partner_id,
                l.price_subtotal as price_total,
                p.default_code as default_code,
                o.name as product_id,
                l.product_qty as product_qty,
                u.name as product_uom,
                y.name as currency_id,
                s.date_order as date_order,
                s.create_date as create_date,
                s.write_date as write_date
            FROM
              purchase_order s 
              left join purchase_order_line as l on (l.order_id = s.id)
              left join res_company as r on (r.id = s.company_id)
              left join product_product as p on (p.id = l.product_id)
              left join product_template as o on (o.id = p.product_tmpl_id)
              left join res_partner as e on (e.id = s.partner_id)
              left join res_currency as y on (l.currency_id = y.id)
              left join uom_uom as u on (u.id = l.product_uom)
              )
        """)


class StockPickingDatabaseView(models.Model):
    _name = "stock.picking.database.view"
    _auto = False

    company_vat = fields.Char(string=u'税号')
    company_id = fields.Many2one('res.company', 'Company')
    name = fields.Char('Reference')
    create_date = fields.Datetime(string=u"创建日期")
    ems_type = fields.Boolean(string=u'有无账册类型')
    ems_no = fields.Char(string=u'金二账册编号')
    warehouse_cd1 = fields.Char(string=u'仓库代码')
    default_code = fields.Char('Internal Reference')
    product_id = fields.Many2one('product.product', 'Product')
    product_uom_qty = fields.Float('Initial Demand')
    product_uom = fields.Many2one('uom.uom', 'Unit of Measure')
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse')
    location_dest_id = fields.Many2one('stock.location',"Destination Location")
    origin = fields.Char('Source Document')
    rlt_no = fields.Char(string=u'收货关联单证编号')
    scheduled_date = fields.Datetime('Scheduled Date')
    write_date = fields.Datetime(string=u"最后更新日期")

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'stock_picking_database_view')
        self.env.cr.execute("""
           CREATE OR REPLACE VIEW stock_picking_database_view AS
           (SELECT
                r.vat as company_vat,
                s.name as name,
                s.p_rlt_no as rlt_no,
                r.name as company_id,
                s.create_date as create_date,
                p.default_code as default_code,
                o.name as product_id,
                m.product_uom_qty as product_uom_qty,
                u.name as product_uom,
                n.name as location_dest_id,
                s.origin as origin,
                s.scheduled_date as scheduled_date,
                s.write_date as write_date,
                s.warehouse_cd1 as warehouse_id,
                r.ems_type as ems_type,
                r.ems_no as ems_no,
                s.picking_t1
            FROM
              stock_picking s 
              left join stock_move as m on (m.picking_id = s.id)
              left join product_product as p on (p.id = m.product_id)
              left join product_template as o on (o.id = p.product_tmpl_id)
              left join res_company as r on (r.id = m.company_id)
              left join stock_warehouse as w on (w.id = m.warehouse_id)
              left join stock_location as n on (n.id = s.location_dest_id)
              left join uom_uom as u on (u.id = m.product_uom)
            WHERE s.picking_t1 = '1')
        """)


class SaleOrderDatabaseView(models.Model):
    _name = "sale.order.database.view"
    _auto = False

    company_vat = fields.Char(string=u'公司税号')
    partner_vat = fields.Char(string=u'供应商税号')
    company_id = fields.Many2one('res.company', 'Company')
    name = fields.Char(string='Order Reference')
    create_date = fields.Datetime(string=u"创建日期")
    partner_id = fields.Many2one('res.partner', string='Customer')
    default_code = fields.Char('Internal Reference', index=True)
    product_id = fields.Many2one('product.product', 'Product')
    product_uom_qty = fields.Float(string='Ordered Quantity')
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure')
    amount_total = fields.Monetary(string='Total')
    currency_id = fields.Many2one(string='Currency')
    expected_date = fields.Datetime("Expected Date")
    write_date = fields.Datetime(string=u"最后更新时间")

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'sale_order_database_view')
        self.env.cr.execute("""
           CREATE OR REPLACE VIEW sale_order_database_view AS
           (SELECT 
                r.vat as company_vat,
                t.vat as partner_vat,
                r.name as company_id,
                s.name as name,
                s.create_date as create_date,
                t.name as partner_id,
                p.default_code as default_code,
                o.name as product_id,
                l.product_uom_qty as product_uom_qty,
                m.name as product_uom,
                s.amount_total as amount_total,
                s.expected_date as expected_date,
                y.name as currency_id,
                s.write_date as write_date
           FROM 
             sale_order s
            LEFT JOIN sale_order_line as l on(l.order_id = s.id)
            left join res_company as r on (r.id = s.company_id)
            left join product_product as p on (p.id = l.product_id)
            left join product_template as o on (o.id = p.product_tmpl_id)
            left join res_partner as t on (t.id = s.partner_id)
            left join res_currency as y on (y.id = l.currency_id)
            left join uom_uom as m on (m.id = l.product_uom)
            )
        """)


class StockPickingOutDatabaseView(models.Model):
    _name = "stock.picking.out.database.view"
    _auto = False

    company_vat = fields.Char(string=u'税号')
    company_id = fields.Many2one('res.company', 'Company')
    name = fields.Char('Reference')
    date_done = fields.Datetime('Date of Transfer')
    default_code = fields.Char('Internal Reference')
    product_id = fields.Many2one('product.product', 'Product')
    product_uom_qty = fields.Float('Initial Demand')
    product_uom = fields.Many2one('uom.uom', 'Unit of Measure')
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse')
    location_id = fields.Many2one('stock.location', "Source Location")
    origin = fields.Char('Source Document')
    scheduled_date = fields.Datetime('Scheduled Date')
    write_date = fields.Datetime(string=u"最后更新日期")
    ems_type = fields.Boolean(string=u'有无账册类型')
    ems_no = fields.Char(string=u'金二账册编号')
    warehouse_cd = fields.Char(string=u'仓库代码')
    rlt_no = fields.Char(string=u'关联单证编号')

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'stock_picking_out_database_view')
        self.env.cr.execute("""
           CREATE OR REPLACE VIEW stock_picking_out_database_view AS
           (SELECT 
                r.vat as company_vat,
                r.name as company_id,
                s.name as name,
                s.date_done as date_done,
                r.ems_type as ems_type,
                r.ems_no as ems_no,
                s.s_rlt_no as rlt_no,
                s.warehouse_cd as warehouse_id,
                p.default_code as default_code,
                o.name as product_id,
                m.product_uom_qty as product_uom_qty,
                u.name as product_uom,
                l.name as location_id,
                s.origin as origin,
                s.scheduled_date as scheduled_date,
                s.write_date as write_date,
                s.picking_t
           FROM 
             stock_picking s
             LEFT join stock_move as m on (m.picking_id = s.id)  
             left join res_company as r on (r.id = s.company_id)
             left join product_product as p on (p.id = m.product_id)
             left join product_template as o on (o.id = p.product_tmpl_id)
             left join stock_location as l on (l.id = m.location_id)
             left join stock_warehouse as w on (w.id = m.warehouse_id)
             left join uom_uom as u on (u.id = m.product_uom)
           WHERE s.picking_t = '1')
           
        """)


class DeliveryDatabaseView(models.Model):
    _name = "delivery.database.view"
    _auto = False

    enterp_cd = fields.Char(string=u'企业编号')
    enterp_nm = fields.Char(string=u'企业名称')
    logistics_no = fields.Char(string=u'物流运单编号')
    logistics_cd = fields.Char(string=u'物流企业代码')
    logistics_nm = fields.Char(string=u'物流企业名称')
    elist_no = fields.Char(string=u'申报清单')
    handlingout_id = fields.Char(string=u'出仓单号')
    gross_wt = fields.Float(string=u'毛重')
    pack_no = fields.Float(string=u'件数')
    goods_info = fields.Char(string=u'主要货物信息')
    origin_stock_picking = fields.Many2one('stock.picking', string=u'源出仓单')
    data_business_time = fields.Datetime(string=u'企业数据业务日期')
    data_update_time = fields.Datetime(string=u'企业数据更新日期')
    data_sync_time = fields.Datetime(string=u'企业数据同步时间')
    # elt_dt = fields.Datetime(string=u'海关采集数据日期')

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'delivery_database_view')
        self.env.cr.execute("""
           CREATE OR REPLACE VIEW delivery_database_view AS
           (SELECT 
                d.enterp_cd as enterp_cd,
                d.enterp_nm as enterp_nm,
                d.logistics_no as logistics_no,
                d.logistics_cd as logistics_cd,
                d.logistics_nm as logistics_nm,
                d.elist_no as elist_no,
                d.handlingout_id as handlingout_id,
                d.gross_wt as gross_wt,
                d.pack_no as pack_no,
                d.goods_info as goods_info,
                d.origin_stock_picking as origin_stock_picking,
                d.create_date as data_business_time,
                d.write_date as data_update_time,
                d.data_sync_time as data_sync_time
           FROM delivery_table d)
        """)


class StockQuantDatabaseView(models.Model):
    _name = "stock.quant.database.view"
    _auto = False

    company_vat = fields.Char(string=u'公司税号')
    company_id = fields.Many2one(string='Company')
    partner_vat = fields.Char(string=u'供应商税号')
    default_code = fields.Char('Internal Reference')
    product_id = fields.Many2one('product.product', 'Product')
    quantity = fields.Float('Quantity')
    product_uom_id = fields.Many2one('uom.uom', 'Unit of Measure')
    owner_id = fields.Many2one('res.partner', 'Owner')
    location_id = fields.Many2one('stock.location', 'Location')
    create_date = fields.Datetime(string=u"创建日期")
    write_date = fields.Datetime(string=u"最后更新时间")
    warehouse_type = fields.Selection([(u'有账册保税', u'有账册保税'), (u'无账册保税', u'无账册保税'), (u'非保税', u'非保税')], string=u'库位标识')
    warehouse_property = fields.Selection([(u'库存区', u'库存区'), (u'其他区', u'其他区')], string=u'库位属性')
    ems_no = fields.Char(string=u'金二账册编号')
    warehouse_cd = fields.Char(string=u'仓库代码')

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'stock_quant_database_view')
        self.env.cr.execute("""
           CREATE OR REPLACE VIEW stock_quant_database_view AS
           (SELECT 
                r.vat as company_vat,
                r.name as company_id,
                e.vat as partner_vat,
                p.default_code as default_code,
                o.name as product_id,
                q.quantity as quantity,
                u.name as product_uom_id,
                q.warehouse_cd as warehouse_id,
                e.name as owner_id,
                s.name as location_id,
                q.create_date as create_date,
                q.write_date as write_date,
                q.warehouse_type as warehouse_type,
                q.warehouse_property as warehouse_property,
                r.ems_no as ems_no
           FROM 
             stock_quant q
             left join res_company as r on (r.id = q.companys_id)
             left join product_product as p on (p.id = q.product_id)
             left join product_template as o on (o.id = p.product_tmpl_id)
             left join stock_location as s on (s.id = q.location_id)
             left join res_partner as e on (e.id = q.owner_id)
             left join uom_uom as u on (u.id = q.product_uom_id)
             )
        """)


class StockMoveLineDatabaseView(models.Model):
    _name = "stock.move.line.database.view"
    _auto = False

    company_vat = fields.Char(string=u'税号')
    company_id = fields.Many2one(string='Company')
    location_id = fields.Many2one('stock.location', 'From')
    location_dest_id = fields.Many2one('stock.location', 'To')
    default_code = fields.Char('Internal Reference')
    product_id = fields.Many2one('product.product', 'Product')
    qty_done = fields.Float('Done')
    product_uom_id = fields.Many2one('uom.uom', 'Unit of Measure')
    create_date = fields.Datetime(string=u"创建日期")
    write_date = fields.Datetime(string=u"最后更新时间")
    uuid = fields.Char(string=u'货物移动流水号')
    in_rack_date = fields.Datetime(string=u'目标库位上架时间')
    out_rack_date = fields.Datetime(string=u'源库位下架时间')

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'stock_move_line_database_view')
        self.env.cr.execute("""
           CREATE OR REPLACE VIEW stock_move_line_database_view AS
           (SELECT 
                r.vat as company_vat,
                r.name as company_id,
                o.name as location_id,
                t.name as location_dest_id,
                p.default_code as default_code,
                s.name as product_id,
                l.move_num as uuid,
                l.qty_done as qty_done,
                u.name as product_uom_id,
                l.create_date as create_date,
                l.write_date as write_date,
                l.in_rack_date as in_rack_date,
                l.out_rack_date as out_rack_date
           FROM 
             stock_move_line l
             left join stock_move as m on (m.id = l.picking_id)
             left join res_company as r on (r.id = l.companys_id)
             left join product_product as p on (p.id = l.product_id)
             left join product_template as s on (s.id = p.product_tmpl_id)
             left join stock_location as o on (o.id = l.location_id)
             left join stock_location as t on (t.id = l.location_dest_id)
             left join uom_uom as u on (u.id = l.product_uom_id)
             )
        """)


class ProductTemplateDatabaseView(models.Model):
    _name = "product.template.database.view"
    _auto = False

    company_vat = fields.Char(string=u'税号')
    company_id = fields.Many2one('res.company', 'Company')
    default_code = fields.Char('Internal Reference')
    name = fields.Char('Name')
    uom_id = fields.Many2one('uom.uom', 'Unit of Measure')
    list_price = fields.Float('Sales Price')
    create_date = fields.Datetime(string=u"创建日期")
    write_date = fields.Datetime(string=u"最后更新时间")
    ems_no = fields.Char(string=u'金二账册编号')
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
    currency_id = fields.Selection([('AUD', 'AUD'),
                                    ('CNY', 'CNY'),
                                    ('EUR', 'EUR'),
                                    ('GBP', 'GBP'),
                                    ('HKD', 'HKD'),
                                    ('JPY', 'JPY'),
                                    ('KRW', 'KRW'),
                                    ('TWD', 'TWD'),
                                    ('USD', 'USD'), ], string=u'币种')

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'product_template_database_view')
        self.env.cr.execute("""
           CREATE OR REPLACE VIEW product_template_database_view AS
           (SELECT 
                r.vat as company_vat,
                r.ems_no as ems_no,
                r.name as company_id,
                p.default_code as default_code,
                p.name as name,
                p.gds_seqno as gds_seqno,
                p.gds_mtno as gds_mtno,
                p.code_ts as code_ts,
                p.gds_name as gds_name,
                p.gds_model as gds_model,
                p.natcd as natcd,
                u.name as g_unit_id,
                p.g_unit_ratio as g_unit_ratio,
                o.name as unit_1_id,
                p.unit_1_ratio as unit_1_ratio,
                p.currency_id as currency_id,
                y.name as uom_id,
                p.list_price as list_price,
                p.create_date as create_date,
                p.write_date as write_date
           FROM 
             product_template p
             left join res_company as r on (r.id = p.company_id)
             left join res_currency as y on (y.id = p.uom_id)
             left join uom_uom as u on (u.id = p.g_unit_id)
             left join uom_uom as o on (u.id = p.unit_1_id)
             )
        """)




