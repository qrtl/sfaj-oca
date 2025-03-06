# Copyright 2024 Quartile
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class AccountBillingTaxAdjustment(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Partner",
            }
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
            }
        )
        cls.journal = cls.env["account.journal"].search(
            [("company_id", "=", cls.env.company.id), ("type", "=", "general")], limit=1
        )
        cls.tax_15 = cls.env["account.tax"].search([("amount", "=", 15.0)], limit=1)
        cls.tax_10 = cls.env["account.tax"].create(
            {"name": "Test Tax 10%", "amount": 10.0, "type_tax_use": "sale"}
        )
        cls.billing_model = cls.env["account.billing"]

    def create_invoice(self, amount, partner, tax):
        """Utility method to create an invoice with a specific amount and tax"""
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": partner,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "quantity": 1,
                            "price_unit": amount,
                            "tax_ids": [(6, 0, tax.ids)],
                        },
                    )
                ],
            }
        )
        invoice.action_post()
        return invoice

    def test_account_billing_tax_adjustments(self):
        inv_1_15 = self.create_invoice(
            amount=200.5, partner=self.partner.id, tax=self.tax_15
        )
        inv_2_15 = self.create_invoice(
            amount=100.5, partner=self.partner.id, tax=self.tax_15
        )
        inv_1_10 = self.create_invoice(
            amount=101.25, partner=self.partner.id, tax=self.tax_10
        )
        inv_2_10 = self.create_invoice(
            amount=203.25, partner=self.partner.id, tax=self.tax_10
        )
        invoices = inv_1_15 + inv_2_15 + inv_1_10 + inv_2_10
        self.assertEqual(inv_1_15.invoice_line_ids.tax_ids.amount, 15.0)
        self.assertEqual(inv_2_15.invoice_line_ids.tax_ids.amount, 15.0)
        self.assertEqual(inv_1_10.invoice_line_ids.tax_ids.amount, 10.0)
        self.assertEqual(inv_2_10.invoice_line_ids.tax_ids.amount, 10.0)
        action = invoices.action_create_billing()
        billing = self.billing_model.browse(action["res_id"])
        self.assertEqual(billing.state, "draft")
        billing.tax_entry_journal_id = self.journal
        billing.validate_billing()
        tax_adjustment_entry = billing.tax_adjustment_entry_id
        self.assertTrue(
            tax_adjustment_entry, "Tax adjustment journal entry should be created."
        )
        tax_adjustment_lines = tax_adjustment_entry.line_ids.filtered(
            lambda line: line.tax_ids
        )
        self.assertEqual(
            len(tax_adjustment_lines),
            2,
            "There should be two tax adjustment lines, one for each tax rate.",
        )
