# -*- coding: utf-8 -*-
###############################################################################
#
# Copyright (C) 2016  Magno Costa - Akretion
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
###############################################################################

from openerp.tests import common


class TestSaleOrderService(common.TransactionCase):

    def setUp(self):
        super(TestSaleOrderService, self).setUp()
        cr, uid = self.cr, self.uid
        # Usefull models
        self.ir_model_data = self.registry('ir.model.data')
        self.sale_order_line = self.registry('sale.order.line')
        self.sale_order = self.registry('sale.order')
        self.account_invoice = self.registry('account.invoice')
        self.product_id = self.ir_model_data.get_object_reference(
            cr, uid, 'product', 'product_product_8')[1]
        self.product_service_id = self.ir_model_data.get_object_reference(
            cr, uid, 'product', 'product_product_consultant')[1]
        # partner Akretion
        self.partner_id = self.ir_model_data.get_object_reference(
            cr, uid, 'l10n_br_base', 'res_partner_akretion')[1]

    def test_sale_order_service(self):
        cr, uid, context = self.cr, self.uid, {}
        # Create sale order with two sale order line

        so_id = self.sale_order.create(
            cr, uid, vals={
                'partner_id': self.partner_id}, context=context)

        obj_sale_order = self.sale_order.browse(
            cr, uid, [so_id], context=context)

        # O onchange abaixo ?? necess??rio para preencher a Posi????o Fiscal
        obj_sale_order.onchange_fiscal()

        self.sale_order_line.create(
            cr, uid,
            values={
                'order_id': so_id,
                'product_id': self.product_id,
                'product_uom_qty': 1,
                'fiscal_category_id': obj_sale_order.fiscal_category_id.id},
            context=context)
        self.sale_order_line.create(
            cr, uid,
            values={
                'order_id': so_id,
                'product_id': self.product_service_id,
                'product_uom_qty': 1,
                'fiscal_category_id': obj_sale_order.fiscal_category_id.id},
            context=context)
        # Confirm sale order
        self.sale_order.action_button_confirm(
            cr, uid, [so_id], context=context)
        # Create Invoice
        self.sale_order.manual_invoice(
            cr, uid, [so_id], context=context)

        for line in obj_sale_order.order_line:
            # O onchange abaixo ?? necess??rio para preencher as Posi????es Fiscais
            line.onchange_fiscal()

        # Verify if the two Invoices were created
        count_invoice = 0
        for order in obj_sale_order.invoice_ids:
            count_invoice += 1
        self.assertTrue(count_invoice == 2)
