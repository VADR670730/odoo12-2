# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import time
import logging

_logger = logging.getLogger(__name__)

class ProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    @api.model
    def get_res2(self,args, name='',args_dict={}, limit=100,name_get_uid=None,operator='ilike',picking_type= None,location_id=False):
        # 构造domain 获取对应的批次号id列表
        args = list(args or [])
        args = args + [("name", operator, name)] if name else args
        access_rights_uid = name_get_uid or self._uid
        lot_ids = self._search(args, limit=None, access_rights_uid=access_rights_uid)
        if lot_ids:
            # 根据批次号的id列表和产品id 获取对应的数量模型（stock.quant）集合

            # 获取location_id
            location_id = args_dict.get('c_location_id') or args_dict.get("parent_location_id",False) or location_id

            location_ids = self.env["stock.location"]._search([["id","child_of",location_id]],limit=None, access_rights_uid=name_get_uid)
            owner_id = args_dict.get('c_owner_id',False)
            product_id = args_dict.get("default_product_id",False)

            if picking_type != "incoming":
                domain = [
                            ["lot_id",'in',lot_ids],["location_id",'in',location_ids],
                            ["quantity", ">", 0],['product_id','=',product_id],
                            ["location_id.usage", '=', "internal"]
                          ]
                if owner_id:
                    domain.append(['owner_id', '=', owner_id])

            else:
                domain = [
                            ['product_id', '=', product_id],["lot_id",'in',lot_ids],
                            ["quantity", ">", 0],["location_id.usage", '=', "internal"]
                        ]

            quantities = self.env["stock.quant"].search(domain, limit=None)

            res = {} if picking_type != "incoming" else {lot_id : 0 for lot_id in lot_ids}

            for quantity in quantities:
                lot_id = quantity.lot_id.id
                res[lot_id] = res.get(lot_id,0) + (quantity.quantity or 0)

            lot_ids = sorted(list(res.keys()),key=lambda x:res[x],reverse=True) if picking_type != "incoming" else lot_ids

            lot_ids = lot_ids[0:limit] if len(lot_ids)>limit else lot_ids


            uom_name = self.env["product.product"].browse(args_dict.get("default_product_id", False)).uom_id.name or "(无单位)"

            lots = self.browse(lot_ids)

            res1 = []
            for lot in lots:
                # " [ 99 件 ]"
                name = " [ %s %s ]"%(str(res.get(lot.id) or "0"),uom_name)
                res1.append((lot.id, lot.name + name))
                # res1.append((lot.id, lot.name + "(" + str(res.get(lot.id) or "0") + uom_name + ")"))

            return res1
        else:
            return []

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None):
        active_view = self._context.get("active_view", False)
        if "view_stock_move_line_operation_tree" == active_view:
            active_picking_id = self._context.get("active_picking_id", False)
            picking = self.env["stock.picking"].browse(active_picking_id) if active_picking_id else False
            picking_type = picking.picking_type_id.code
            return self.get_res2(args, name = name, args_dict = self._context,limit=limit, operator=operator,name_get_uid=name_get_uid,picking_type=picking_type)
        elif "view_mrp_product_produce_wizard" == active_view:
            production_id = self._context.get("production_id")
            location_id = self.env['mrp.production'].browse(production_id).location_src_id.id or False
            return self.get_res2(args, name=name, args_dict=self._context, limit=limit, operator=operator,
                                 name_get_uid=name_get_uid, location_id= location_id)
        else:
            return super(ProductionLot, self).name_search(name=name, args=args, operator=operator, limit=limit)




class Location(models.Model):
    _inherit = "stock.location"

    @api.model
    def get_res(self, name, args, args_dict={}, operator='ilike', limit=100, name_get_uid=None, picking_type = None):

        id = args_dict.get("id")
        args_ = []
        location_ids = self._search(['|', ('barcode', operator, name), ('complete_name', operator, name)] + args,
                                    limit=None, access_rights_uid=name_get_uid)


        if len(location_ids) > 0:
            if args_dict.get("location_type") == "from" and picking_type != "incoming":
                args_ = [["quantity", ">", 0], ["location_id.usage", '=', "internal"],['location_id', "in", location_ids],['product_id','=',args_dict.get('c_product_id',False)]]
                # args_ = [['location_id', "in", location_ids],['product_id','=',args_dict.get('c_product_id',False)]]

                lot_id = args_dict.get('c_lot_id', False)
                if lot_id:
                    args_.append(["lot_id", "=", lot_id])
                owner_id = args_dict.get('c_owner_id', False)
                if owner_id:
                    args_.append(['owner_id', '=', owner_id])
                # args_ = [["quantity", ">", 0], ["location_id.usage", '=', "internal"],
                #      ['location_id', "in", location_ids], ['owner_id','=',args_dict.get('c_owner_id',False)],['product_id','=',args_dict.get('c_product_id')]]
            else:
                args_ = [['location_id', "in", location_ids], ['product_id', '=', args_dict.get('c_product_id')]]

            quantities = self.env["stock.quant"].search(args_, limit=None)

            res = {} if args_dict.get("location_type") == "from" and picking_type != "incoming" else {location_id : 0 for location_id in location_ids}

            for quantity in quantities:
                location_id = quantity.location_id.id
                res[location_id] = res.get(location_id, 0) + (quantity.quantity or 0)

            location_ids = sorted(list(res.keys()),key=lambda x:res[x],reverse=True) if args_dict.get("location_type") == "from" and picking_type != "incoming" else location_ids

            location_ids = location_ids[0:limit] if len(location_ids) > limit else location_ids

            uom_name = self.env["product.product"].browse(args_dict.get("c_product_id", False)).uom_id.name or "(无单位)"
            res["sum"] = sum([res[i] for i in location_ids if res.get(i)]) if res.get(id, None) else 0
            res1 = []

            locations = self.browse(location_ids)
            for location in locations:
                usage = location.usage
                flag = len(location.child_ids)
                if usage and usage == "internal" and location.id == id and flag > 0:
                    # "WH/Stock [ 99 件，库区: 299 件 ]"

                    name = "%s [ %s %s，库区: %s %s ]"%(location.display_name,str(res.get(location.id, 0)),uom_name,str(res.get("sum", 0)),uom_name)

                    # res1.append((location.id, location.display_name + " [ " + str(res.get(location.id, 0)) + (uom_name ) + ")(库区)"))
                    res1.append((location.id, name))


                elif usage and usage == "internal":
                    # "WH/Stock/aaa [ 99 件 ]"

                    name_ = "%s [ %s %s ]" % (location.display_name, str(res.get(location.id, 0)), uom_name)

                    res1.append((location.id, name_))
                    # res1.append((location.id, location.display_name + "(" + str(res.get(location.id, 0)) + (
                    #             uom_name ) + ")"))
                else:
                    res1.append((location.id, location.display_name))

            res1.sort(key=lambda x:x[0])
            return res1

        else:
            return []

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None):
        """ search full name and barcode """
        if args is None:
            args = []
        active_view = self._context.get("active_view", False)
        if "view_stock_move_line_operation_tree" == active_view:
            active_picking_id = self._context.get("active_picking_id", False)
            picking = self.env["stock.picking"].browse(active_picking_id) if active_picking_id else False
            picking_type = picking.picking_type_id.code
            return self.get_res(name, args, args_dict=self._context, operator = 'ilike', limit = limit, name_get_uid = name_get_uid, picking_type = picking_type)
        else:
            return super(Location,self).name_search(name = name, args=args, operator='ilike', limit=100)



class StockMove(models.Model):
    _inherit = "stock.move"


    def action_show_details(self):
        """ Returns an action that will open a form view (in a popup) allowing to work on all the
        move lines of a particular move. This form view is used when "show operations" is not
        checked on the picking type.
        """
        self.ensure_one()

        # If "show suggestions" is not checked on the picking type, we have to filter out the
        # reserved move lines. We do this by displaying `move_line_nosuggest_ids`. We use
        # different views to display one field or another so that the webclient doesn't have to
        # fetch both.
        if self.picking_id.picking_type_id.show_reserved:
            view = self.env.ref('stock.view_stock_move_operations')
        else:
            view = self.env.ref('stock.view_stock_move_nosuggest_operations')

        return {
            'name': _('Detailed Operations'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.move',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.id,
            'context': dict(
                self.env.context,
                show_lots_m2o=self.has_tracking != 'none' and (self.picking_type_id.use_existing_lots or self.state == 'done' or self.origin_returned_move_id.id),  # able to create lots, whatever the value of ` use_create_lots`.
                show_lots_text=self.has_tracking != 'none' and self.picking_type_id.use_create_lots and not self.picking_type_id.use_existing_lots and self.state != 'done' and not self.origin_returned_move_id.id,
                show_source_location= self.picking_type_id.code != 'incoming' and self.location_id.child_ids,
                show_destination_location=self.picking_type_id.code != 'outgoing' and self.location_dest_id.child_ids,
                show_package=not self.location_id.usage == 'supplier',
                # show_reserved_quantity=self.state != 'done',
                show_reserved_quantity=False,
            ),
        }


from collections import defaultdict

class StockMoveLine(models.Model):
    _inherit = "stock.move.line"


    @api.model
    def default_get(self, fields_list):
        self.view_init(fields_list)
        defaults = {}
        parent_fields = defaultdict(list)
        ir_defaults = self.env['ir.default'].get_model_defaults(self._name)

        for name in fields_list:
            # 1. look up context
            key = 'default_' + name
            if key in self._context:
                defaults[name] = self._context[key]
                continue

            # 2. look up ir.default
            if name in ir_defaults:
                defaults[name] = ir_defaults[name]
                continue

            field = self._fields.get(name)

            # 3. look up field.default
            if field and field.default:
                defaults[name] = field.default(self)
                continue

            # 4. delegate to parent model
            if field and field.inherited:
                field = field.related_field
                parent_fields[field.model_name].append(field.name)

        # convert default values to the right format
        defaults = self._convert_to_write(defaults)

        # add default values for inherited fields
        for model, names in parent_fields.items():
            defaults.update(self.env[model].default_get(names))

        active_picking_id = self._context.get("default_picking_id", False)
        if active_picking_id:
            picking = self.env["stock.picking"].browse(active_picking_id) if active_picking_id else False
            picking_type = picking.picking_type_id.code

            if picking_type == "outgoing":
                defaults["location_id"] = False
            elif picking_type == "incoming":
                defaults["location_dest_id"] = False
            elif picking_type == "internal":
                defaults["location_id"] = False
                defaults["location_dest_id"] = False
        return defaults


class Picking(models.Model):
    _inherit = "stock.picking"

    @api.multi
    def _create_backorder(self, backorder_moves=[]):
        """ Move all non-done lines into a new backorder picking.
        """
        backorders = self.env['stock.picking']
        # move_line1 = self.move_lines[0]
        # move_line2 = self.move_lines[1]
        for picking in self:
            moves_to_backorder = picking.move_lines.filtered(lambda x: x.state not in ('done', 'cancel'))
            if moves_to_backorder:
                backorder_picking = picking.copy({
                    'name': '/',
                    'move_lines': [],
                    'move_line_ids': [],
                    'backorder_id': picking.id
                })
                picking.message_post(
                    body=_('The backorder <a href=# data-oe-model=stock.picking data-oe-id=%d>%s</a> has been created.') % (
                        backorder_picking.id, backorder_picking.name))
                moves_to_backorder.write({'picking_id': backorder_picking.id})
                moves_to_backorder.mapped('package_level_id').write({'picking_id':backorder_picking.id})
                moves_to_backorder.mapped('move_line_ids').write({'picking_id': backorder_picking.id})
                # backorder_picking.action_assign()
                backorders |= backorder_picking
        return backorders


from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class PickingType(models.Model):
    _inherit = "stock.picking.type"


    def _compute_picking_count(self):
        # TDE TODO count picking can be done using previous two
        domains = {
            'count_picking_draft': [('state', '=', 'draft')],
            'count_picking_waiting': [('state', 'in', ('confirmed', 'waiting'))],
            # 'count_picking_ready': [('state', '=', 'assigned')],
            'count_picking_ready': [('state', 'in', ('confirmed', 'assigned'))],
            'count_picking': [('state', 'in', ('assigned', 'waiting', 'confirmed'))],
            'count_picking_late': [('scheduled_date', '<', time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)), ('state', 'in', ('assigned', 'waiting', 'confirmed'))],
            'count_picking_backorders': [('backorder_id', '!=', False), ('state', 'in', ('confirmed', 'assigned', 'waiting'))],
        }
        for field in domains:
            data = self.env['stock.picking'].read_group(domains[field] +
                [('state', 'not in', ('done', 'cancel')), ('picking_type_id', 'in', self.ids)],
                ['picking_type_id'], ['picking_type_id'])
            count = {
                x['picking_type_id'][0]: x['picking_type_id_count']
                for x in data if x['picking_type_id']
            }
            for record in self:
                record[field] = count.get(record.id, 0)
        for record in self:
            record.rate_picking_late = record.count_picking and record.count_picking_late * 100 / record.count_picking or 0
            record.rate_picking_backorders = record.count_picking and record.count_picking_backorders * 100 / record.count_picking or 0