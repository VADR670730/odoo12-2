# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _

from odoo.exceptions import AccessError, UserError


class Express(models.Model):
    _name = 'express'
    _description = '快递'
    _rec_name = 'send_person'
    _inherit = ['mail.thread']

    @api.model
    def create(self, vals):
        """
        自动生成编码
        :return:
        """
        # print(self.env.user.name)
        # print(self.env['express'])
        vals['number'] = self.env['ir.sequence'].next_by_code('express') or ''
        return super(Express, self).create(vals)

    # @api.multi
    # def write(self, vals):
    #     return super(Express, self).write(vals)

    number = fields.Char(string=u"自动生成序号", track_visibility="onchange")
    seq = fields.Char(string=u'序号', track_visibility="onchange")
    date = fields.Datetime(string=u'寄件日期', track_visibility="onchange")
    end_date = fields.Datetime(string=u'到货日期', track_visibility="onchange")
    send_person = fields.Char(string=u'寄件人',default=lambda self: self.env.user.name, track_visibility="onchange")
    express_company = fields.Char(string=u'快递公司', track_visibility="onchange")
    money = fields.Float(string=u'运费', track_visibility="onchange")
    destination = fields.Char(string=u'目的地', track_visibility="onchange")
    weight = fields.Float(string=u'结算重量', track_visibility="onchange")

    cus = fields.Char(string=u'客户', track_visibility="onchange")
    express_no = fields.Char(string=u'运单编号', track_visibility="onchange")
    scan_data = fields.Datetime(string=u'扫描时间', track_visibility="onchange")
    scan_person = fields.Char(string=u'扫描人', track_visibility="onchange")
    remark = fields.Char(string=u'备注', track_visibility="onchange")

    # @api.constrains('send_person')
    # def compute_window(self):
    #     for item in self:
    #         if item.date:
    #             print(111)
    #         else:
    #             raise UserError("No Mercury configuration associated with the journal.")
