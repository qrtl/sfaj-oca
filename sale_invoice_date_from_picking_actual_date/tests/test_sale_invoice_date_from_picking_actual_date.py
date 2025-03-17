# Copyright 2025 Quartile (https://www.quartile.co)
# Licence AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).

from datetime import datetime, timedelta

from odoo import Command, fields
from odoo.tests.common import TransactionCase


class TestInvoiceDateFromPickingActualDate(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Test Customer"})
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "product",
                "list_price": 100.0,
            }
        )
        cls.env.company.use_actual_date_for_invoice = True

    def _create_sale_order(self, partner, product, quantity=1):
        order = self.env["sale.order"].create(
            {
                "partner_id": partner.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": product.id,
                            "product_uom_qty": quantity,
                        }
                    )
                ],
            }
        )
        order.action_confirm()
        return order

    def _validate_picking(self, picking):
        picking.move_ids.quantity_done = picking.move_ids.product_uom_qty
        picking.action_confirm()
        picking.action_assign()
        picking.button_validate()

    def test_invoice_date_matches_date_done(self):
        order = self._create_sale_order(self.partner, self.product)
        picking = order.picking_ids[0]
        self._validate_picking(picking)
        invoice = order._create_invoices()
        picking_date = fields.Datetime.context_timestamp(
            order.with_context(tz=order.company_id.partner_id.tz), picking.date_done
        ).date()
        self.assertEqual(
            invoice.invoice_date,
            picking_date,
            "Invoice date should match picking's date_done.",
        )

    def test_invoice_date_matches_actual_date(self):
        order = self._create_sale_order(self.partner, self.product)
        picking = order.picking_ids[0]
        actual_date = (datetime.now() - timedelta(days=2)).date()
        picking.write({"actual_date": actual_date})
        self._validate_picking(picking)
        invoice = order._create_invoices()
        self.assertEqual(
            invoice.invoice_date,
            actual_date,
            "Invoice date should match picking's actual_date.",
        )
