# Copyright 2025 Quartile
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import timedelta

from odoo.tests.common import TransactionCase


class TestSaleLeadTimeProfile(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Partner",
                "country_id": cls.env.ref("base.us").id,
            }
        )
        cls.warehouse = cls.env["stock.warehouse"].create(
            {"name": "Main Warehouse", "code": "MW"}
        )
        cls.lead_time_profile_1 = cls.env["lead.time.profile"].create(
            {
                "country_id": cls.env.ref("base.us").id,
                "lead_time": 3.0,
            }
        )
        cls.lead_time_profile_2 = cls.env["lead.time.profile"].create(
            {
                "warehouse_id": cls.warehouse.id,
                "country_id": cls.env.ref("base.us").id,
                "lead_time": 5.0,
            }
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "product",
            }
        )

    def create_and_confirm_sale_order(self):
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "warehouse_id": self.warehouse.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": self.product.name,
                            "product_id": self.product.id,
                            "product_uom_qty": 2,
                            "product_uom": self.product.uom_id.id,
                            "price_unit": self.product.list_price,
                        },
                    )
                ],
            }
        )
        sale_order.action_confirm()
        return sale_order

    def test_sale_order_lead_time_profile(self):
        sale_order = self.create_and_confirm_sale_order()
        self.assertTrue(sale_order.picking_ids)
        self.assertEqual(sale_order.delivery_lead_time, 5.0)
        self.assertEqual(sale_order.order_line.customer_lead, 5.0)
        picking = sale_order.picking_ids
        self.assertEqual(
            picking.scheduled_date.date() + timedelta(days=5.0),
            picking.date_deadline.date(),
        )

        # assign partner_id to profile
        self.lead_time_profile_1.partner_id = self.partner.id
        sale_order = self.create_and_confirm_sale_order()
        self.assertTrue(sale_order.picking_ids)
        self.assertEqual(sale_order.delivery_lead_time, 3.0)
        self.assertEqual(sale_order.order_line.customer_lead, 3.0)
        picking = sale_order.picking_ids
        self.assertEqual(
            picking.scheduled_date.date() + timedelta(days=3.0),
            picking.date_deadline.date(),
        )
