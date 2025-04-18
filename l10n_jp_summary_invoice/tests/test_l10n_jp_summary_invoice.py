# Copyright 2024 Quartile
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError
from odoo.fields import Command
from odoo.tests.common import TransactionCase


class TestSummaryInvoice(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})
        cls.bank_account = cls.env["res.partner.bank"].create(
            {
                "partner_id": cls.env.company.partner_id.id,
                "acc_number": "1234567890",
            }
        )
        cls.product = cls.env["product.product"].create({"name": "Test Product"})
        cls.tax_15 = cls.env["account.tax"].search([("amount", "=", 15.0)], limit=1)

    def _create_invoice(self, amount, tax, partner=None, bank=None):
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": partner or self.partner.id,
                "partner_bank_id": bank and bank.id,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": self.product.id,
                            "quantity": 1,
                            "price_unit": amount,
                            "tax_ids": [Command.set(tax.ids)],
                        }
                    )
                ],
            }
        )
        invoice.action_post()
        return invoice

    def test_constrains_invoice_not_for_billing(self):
        invoice = self._create_invoice(100, self.tax_15)
        invoice.write({"is_not_for_billing": True})

        with self.assertRaises(ValidationError):
            self.env["account.billing"].create(
                {
                    "partner_id": self.partner.id,
                    "billing_line_ids": [Command.create({"move_id": invoice.id})],
                }
            )

    def test_constrains_remit_to_bank_conflict(self):
        invoice = self._create_invoice(100, self.tax_15, bank=self.bank_account)
        other_bank = self.env["res.partner.bank"].create(
            {
                "partner_id": self.env.company.partner_id.id,
                "acc_number": "other_bank_acc",
            }
        )

        with self.assertRaises(ValidationError):
            self.env["account.billing"].create(
                {
                    "partner_id": self.partner.id,
                    "remit_to_bank_id": other_bank.id,
                    "billing_line_ids": [Command.create({"move_id": invoice.id})],
                }
            )

    def test_compute_billing_due_date(self):
        inv1 = self._create_invoice(100, self.tax_15)
        inv2 = self._create_invoice(200, self.tax_15)
        inv1.invoice_date_due = inv1.invoice_date_due.replace(day=5)
        inv2.invoice_date_due = inv2.invoice_date_due.replace(day=25)
        billing = self.env["account.billing"].create(
            {
                "partner_id": self.partner.id,
                "billing_line_ids": [
                    Command.create({"move_id": inv1.id}),
                    Command.create({"move_id": inv2.id}),
                ],
            }
        )
        self.assertEqual(billing.date_due, inv2.invoice_date_due)

    def test_update_remit_to_bank_defaulting(self):
        invoice = self._create_invoice(100, self.tax_15, bank=self.bank_account)
        billing = self.env["account.billing"].create(
            {
                "partner_id": self.partner.id,
                "billing_line_ids": [Command.create({"move_id": invoice.id})],
            }
        )
        self.assertEqual(billing.remit_to_bank_id, self.bank_account)

    def test_get_moves_filters_billed_and_flags(self):
        billed_invoice = self._create_invoice(50, self.tax_15)
        billed_invoice.write({"is_not_for_billing": True})
        billing = self.env["account.billing"].create(
            {
                "partner_id": self.partner.id,
            }
        )
        moves = billing._get_moves()
        self.assertNotIn(billed_invoice.id, moves.ids)

    def test_create_tax_adjustment_entry(self):
        inv_1_15 = self._create_invoice(200.5, self.tax_15)
        inv_2_15 = self._create_invoice(100.5, self.tax_15)
        invoices = inv_1_15 + inv_2_15
        self.assertEqual(inv_1_15.invoice_line_ids.tax_ids.amount, 15.0)
        self.assertEqual(inv_2_15.invoice_line_ids.tax_ids.amount, 15.0)
        action = invoices.action_create_billing()
        billing = self.env["account.billing"].browse(action["res_id"])
        self.assertEqual(billing.state, "draft")
        billing.validate_billing()
        tax_adjustment_entry = billing.tax_adjustment_entry_id
        self.assertTrue(
            tax_adjustment_entry, "Tax adjustment journal entry should be created."
        )
