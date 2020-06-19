# -*- encoding: utf-8 -*-
import time, datetime
from collections import defaultdict, OrderedDict
from operator import itemgetter
from itertools import groupby
import math
from odoo import models, fields, api, _, tools, SUPERUSER_ID
import odoo.addons.decimal_precision as dp
from odoo.tools import float_compare, float_round, float_is_zero
from odoo.exceptions import UserError, ValidationError



class partner_product_pricelist(models.AbstractModel):
    _name = 'partner.product.pricelist'
    _description = u'客户产品价格查询'

    @api.multi
    def _compute_price_22(self):
        for x in self:
            x.price_11 = "%.4f(%s)" % (x.price_1,x.currency_id.name)
            x.price_22 = "%.4f(%s)" % (x.price_2,x.currency_id.name)
            x.price_33 = "%.4f(%s)" % (x.price_3,x.currency_id.name)

    @api.multi
    def _compute_discount_price_22(self):
        for x in self:
            x.discount_price_22 = "%.4f %%" % (x.discount_price_2,)
            x.discount_price_33 = "%.4f %%" % (x.discount_price_3,)

    partner_id = fields.Many2one('res.partner', u'客户')
    partner_product_id = fields.Many2one('res.partner.product', u'客户产品')
    product_id = fields.Many2one('product.product', u'我司产品')
    currency_id = fields.Many2one('res.currency', 'Currency')
    price_1 = fields.Float(u'零售价', digits=dp.get_precision('Product Price'))
    price_2 = fields.Float(u'供货价', digits=dp.get_precision('Product Price'))
    price_3 = fields.Float(u'结算价', digits=dp.get_precision('Product Price'))
    discount_price_2 = fields.Float(u'供货价%', digits=dp.get_precision('Discount'))
    discount_price_3 = fields.Float(u'结算价%', digits=dp.get_precision('Discount'))
    discount_price_22 = fields.Char(u'前台点数', compute='_compute_discount_price_22')
    discount_price_33 = fields.Char(u'后台点数', compute='_compute_discount_price_22')
    price_11 = fields.Char(u'零售价', compute='_compute_price_22')
    price_22 = fields.Char(u'供货价', compute='_compute_price_22')
    price_33 = fields.Char(u'结算价', compute='_compute_price_22')
    date_start = fields.Date(u'时间起')
    date_end = fields.Date(u'时间止')


    def init(self):
        tools.drop_view_if_exists(self._cr, 'partner_product_pricelist')
        self._cr.execute("""create or replace view partner_product_pricelist as (

                  select bb.id,bb.partner_id,bb.product_id,cc.id as partner_product_id,currency_id,price1 as price_1,discount2 as discount_price_2,price2 as price_2,discount3 as discount_price_3,price3  as price_3,
                        bb.date_start,bb.date_end
                    from (
                            select min(id) as id,partner_id,product_id,currency_id
                                ,max(coalesce(price1,0)) as price1
                                ,case when max(coalesce(price1,0.0))=0.0 or max(coalesce(price2,0.0))=0.0 then 0.0::numeric(16,4) else round((max(coalesce(price1,0.0))-max(coalesce(price2,0.0)))::numeric(16,4)/max(coalesce(price1,0.0))::numeric(16,4)*100.0,4) end as discount2
                                ,sum(coalesce(price2,0)) as price2
                                ,case when max(coalesce(price2,0.0))=0.0 or max(coalesce(price3,0.0))=0.0 then 0.0::numeric(16,4) else round((max(coalesce(price2,0.0))-max(coalesce(price3,0.0)))::numeric(16,4)/max(coalesce(price2,0.0))::numeric(16,4)*100.0,4) end as discount3
                                ,sum(coalesce(price3,0)) as price3
                                ,max(aa.date_start) as date_start,min(aa.date_start) as date_end
                             from (
                                select b.id*a.id+b.product_id as id,a.id as partner_id,product_id,price::numeric(16,4) as price1,cast(0.0 as  numeric(16,4)) as price2,cast(0.0 as numeric(16,4)) as price3,date_start,date_end
                                       ,b.currency_id
                                  from res_partner a , product_pricelist_list b
                                 where a.customer='t'
                                   and a.property_product_pricelist1=b.pricelist_id
                                   and a.active='t'
                                   and a.property_product_pricelist1 is not null
                                   and a.id not in (select partner_id from res_users)
                                   and a.is_company='t'
                                   and COALESCE (a.not_show_in_product_pricelist,'f')='f'
                                union
                                select b.id*a.id+b.product_id as id,a.id as partner_id,product_id,cast(0.0 as  numeric(16,4))  as price1,price::numeric(16,4) as price2,cast(0.0 as numeric(16,4)) as price3,date_start,date_end
                                                      ,b.currency_id
                                  from res_partner a , product_pricelist_list b
                                 where a.customer='t'
                                   and a.property_product_pricelist2=b.pricelist_id
                                   and a.active='t'
                                   and a.property_product_pricelist2 is not null
                                   and a.id not in (select partner_id from res_users)
                                   and a.is_company='t'
                                   and COALESCE (a.not_show_in_product_pricelist,'f')='f'
                                union
                                select b.id*a.id+b.product_id as id,a.id as partner_id,product_id,cast(0.0 as  numeric(16,4)) as price1,cast(0.0 as  numeric(16,4)) as price2,price::numeric(16,4) as price3,date_start,date_end
                                                       ,b.currency_id
                                  from res_partner a , product_pricelist_list b
                                 where a.customer='t'
                                   and a.property_product_pricelist3=b.pricelist_id
                                   and a.active='t'
                                   and a.property_product_pricelist3 is not null
                                   and a.id not in (select partner_id from res_users)
                                   and a.is_company='t'
                                   and COALESCE (a.not_show_in_product_pricelist,'f')='f'
                                ) aa
                             group by partner_id,product_id,currency_id
                        ) bb left join res_partner_product cc on  bb.partner_id=cc.partner_id and bb.product_id=cc.product_id
                        where bb.partner_id not in (select partner_id from res_users)
                )
        """)