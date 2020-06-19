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


class product_pricelist(models.Model):
    _inherit = 'product.pricelist'
    _description = u'价格表'

    llc = fields.Integer(u'LLC')

    @api.multi
    def compute_product_pricelist_list(self):
        self._cr.execute("""
            select update_llc_from_pricelist();
            delete from product_pricelist_list;
        """)
        objs=self.env['product.pricelist'].search([],order='llc')
        for x in objs:
            x.compute_product_pricelist_list_one()

    @api.multi
    def compute_product_pricelist_list_one(self):
        self.ensure_one()
        self._cr.execute("""
        delete from product_pricelist_list where pricelist_id=%s
        """ % (self.id,))
        product_pricelist_lists = []
        today = fields.Date.context_today(self)
        for item in self.item_ids:  # 生失效日期
            if today < item.date_start or (item.date_end < today and item.date_end):
                continue
            products_qty_partners = []
            if item.applied_on == '0_product_variant' and item.product_id:
                products_qty_partners = [(item.product_id, 1.0, None)]
            elif item.applied_on == '1_product' and item.product_tmpl_id:
                products_qty_partners = [(p, 1.0, None) for p in item.product_tmpl_id.product_variant_ids]
            elif item.applied_on == '2_product_category' and item.categ_id:
                objs = self.env['product.product'].search([('categ_id', '=', item.categ_id.id)])
                products_qty_partners = [(p, 1.0, None) for p in objs]
            else:
                objs = self.env['product.product'].search([])
                products_qty_partners = [(p, 1.0, None) for p in objs]

            for products_qty_partner in products_qty_partners:
                result = self._compute_price_rule([products_qty_partner])
                for k, v in result.iteritems():
                    product_pricelist_lists.append((self.id,self.currency_id.id, k, v[0], item.date_start or None, item.date_end or None))
        if product_pricelist_lists:
            self._cr.executemany(
                'insert into product_pricelist_list (pricelist_id,currency_id,product_id,price,date_start,date_end) values (%s,%s,%s,%s,%s,%s)',
                product_pricelist_lists)

    def init(self):
        self._cr.execute("""
            CREATE OR REPLACE FUNCTION public.update_llc_from_pricelist()
              RETURNS void AS
            $BODY$
                DECLARE
                /*
                  由 pricelist 计算 pricelist LLC
                  select update_llc_from_pricelist()
                  select llc from product_pricelist
                */
                    -- 声明段
                BEGIN
                   create local temporary table if not exists tmp_pro (id integer, llc integer);
                   insert into tmp_pro( id, llc)
                   select id,0 as llc
                     from product_pricelist;

                   create local temporary table if not exists tmp_wo (product_id integer,  material integer,llc integer);
                   insert into tmp_wo (product_id, material,llc)
                   select distinct base_pricelist_id as parent_id,pricelist_id, 0 as llc--,date_start,date_end
                    from product_pricelist_item
                   where base='pricelist'
                     and base_pricelist_id is not null
                     and pricelist_id is not null
                     and pricelist_id<>base_pricelist_id;
                     --and ((current_date between date_start and date_end) or (date_start <=current_date and date_start is null));

                     WITH RECURSIVE LowerLevelCode(id, llc) AS (
                   SELECT id,max(llc)
                     FROM tmp_pro a
                    group by id
                    UNION ALL
                   SELECT a.material,b.llc + 1
                     FROM tmp_wo a,LowerLevelCode b
                    WHERE a.product_id= b.id
                      and b.llc<10
                    )
                   update tmp_pro set LLC=( select Max(LLC) as LLc
                                              from LowerLevelCode
                                             group by id
                                            having tmp_pro.id= LowerLevelCode.id);

                  update product_pricelist set llc=0;
                  update product_pricelist a set llc=b.llc
                    from tmp_pro b
                   where a.id=b.id;

                  drop table tmp_pro;
                  drop table tmp_wo;
                END;
                $BODY$
              LANGUAGE plpgsql VOLATILE
              COST 100;

        """)


class PricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    percent_price = fields.Float('Percentage Price',digits=dp.get_precision('Discount'))