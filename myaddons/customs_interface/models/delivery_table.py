# -*- coding: utf-8 -*-

from odoo import models, fields, api


class DeliveryTable(models.Model):
    _name = 'delivery.table'
    _rec_name = "logistics_no"

    @api.model
    def create(self, vals):

        return super(DeliveryTable).create(vals)

    @api.model
    def create(self, vals):
        """
        自动生成运单编码
        :return:
        """
        vals['logistics_no'] = self.env['ir.sequence'].next_by_code('delivery.table') or ''
        obj = super(DeliveryTable, self).create(vals)
        # self.compute_origin(obj)
        if obj.logistics_cd:
            print('obj')
            obj.logistics_no = 'WL/' + obj.logistics_cd + obj.logistics_no
        return obj

    def compute_origin(self, obj):
        print(obj.origin_stock_picking.id)
        if obj.origin_stock_picking:
            stock_out_obj = self.env['stock.picking'].search([('id', '=', obj.origin_stock_picking.id)], limit=1)
            print('stock_out_obj', stock_out_obj.id)
            stock_out_obj.logistics_no = obj.logistics_no
            stock_out_obj.logistics_cd = obj.logistics_cd
            stock_out_obj.logistics_nm_id = obj.logistics_nm_id
            stock_out_obj.handlingin_id = obj.handlingout_id

    enterp_cd = fields.Char(string=u'企业编号', default=lambda self: self.env.user.company_id.vat)
    enterp_nm = fields.Char(string=u'企业名称', default=lambda self: self.env.user.company_id.name)
    logistics_no = fields.Char(string=u'物流运单编号')
    logistics_cd = fields.Char(string=u'物流企业代码')
    logistics_nm = fields.Char(string=u'物流企业名称')
    elist_no = fields.Char(string=u'申报清单')
    handlingout_id = fields.Char(string=u'出仓单号')
    gross_wt = fields.Float(string=u'毛重')
    pack_no = fields.Float(string=u'件数')
    goods_info = fields.Text(string=u'主要货物信息')
    origin_stock_picking = fields.Many2one('stock.picking', string=u'源出仓单')
    data_business_time = fields.Datetime(string=u'企业数据业务日期')
    data_update_time = fields.Datetime(string=u'企业数据更新日期')
    data_sync_time = fields.Datetime(string=u'企业数据同步时间')
    # elt_dt = fields.Datetime(string=u'海关采集数据日期')

