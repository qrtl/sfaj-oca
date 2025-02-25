# Copyright 2024-2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import Command, _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_round


class AccountBilling(models.Model):
    _inherit = "account.billing"

    # FIXME: Remove these fields
    amount_untaxed = fields.Monetary(compute="_compute_amount", store=True)
    total_amount = fields.Monetary(compute="_compute_amount", store=True)
    taxes = fields.Char(string="Tax", compute="_compute_amount", store=True)

    # Just changing the default value
    threshold_date_type = fields.Selection(default="invoice_date")
    date_due = fields.Date(
        compute="_compute_billing_date_due",
        store=True,
        readonly=False,
        states={"draft": [("readonly", False)]},
        index=True,
        copy=False,
    )
    tax_totals = fields.Binary(
        string="Billing Totals",
        compute="_compute_tax_totals",
        exportable=False,
    )
    tax_adjustment_entry_id = fields.Many2one("account.move")
    tax_entry_journal_id = fields.Many2one(
        "account.journal",
        help="This journal will be used for tax adjustment journal entry.",
    )
    company_partner_id = fields.Many2one(related="company_id.partner_id", store=True)
    remit_to_bank_id = fields.Many2one(
        "res.partner.bank",
        "Remit-to Bank",
        domain="[('partner_id', '=', company_partner_id)]",
        help="If not specified, the first bank account linked to the company will show "
        "in the report.",
    )

    @api.constrains("state", "billing_line_ids")
    def _check_account_move_billability(self):
        for rec in self:
            invoices = rec.billing_line_ids.move_id
            if invoices.filtered(
                lambda x: len(x.billing_ids.filtered(lambda x: x.state != "cancel")) > 1
            ):
                raise ValidationError(
                    _("An invoice can only be included in one billing.")
                )

    @api.depends("billing_line_ids")
    def _compute_billing_date_due(self):
        for billing in self:
            if not billing.billing_line_ids:
                continue
            billing.date_due = max(
                move.invoice_date_due for move in billing.billing_line_ids.move_id
            )

    @api.depends("billing_line_ids.move_id")
    def _compute_amount(self):
        for billing in self:
            amount_untaxed = 0.0
            total_amount = 0.0
            taxes_set = set()
            for line in billing.billing_line_ids:
                amount_untaxed += line.move_id.amount_untaxed
                total_amount += line.move_id.amount_total
                for invoice_line in line.move_id.invoice_line_ids:
                    if invoice_line.tax_ids:
                        for tax in invoice_line.tax_ids:
                            tax_name = tax.description or tax.name
                            taxes_set.add(tax_name)
            billing.amount_untaxed = amount_untaxed
            billing.total_amount = total_amount
            billing.taxes = ", ".join(sorted(taxes_set))

    @api.depends_context("lang")
    @api.depends(
        "billing_line_ids",
        "partner_id",
        "currency_id",
    )
    def _compute_tax_totals(self):
        for bill in self:
            invoice_lines = bill.billing_line_ids.move_id.invoice_line_ids
            base_lines = invoice_lines.filtered(
                lambda line: line.display_type == "product"
            )
            base_line_values_list = [
                line._convert_to_tax_base_line_dict() for line in base_lines
            ]
            kwargs = {
                "base_lines": base_line_values_list,
                "currency": bill.currency_id or bill.company_id.currency_id,
            }
            kwargs["tax_lines"] = [
                line._convert_to_tax_line_dict()
                for line in invoice_lines.filtered(
                    lambda line: line.display_type == "tax"
                )
            ]
            bill.tax_totals = self.env["account.tax"]._prepare_tax_totals(**kwargs)

    def _get_moves(self, date=False, types=False):
        moves = super()._get_moves(date=date, types=types)
        # Prevent the billing from adding already billed invoices
        moves -= moves.filtered(
            lambda x: x.billing_ids.filtered(lambda x: x.state != "cancel")
        )
        return moves

    def _get_tax_summary_from_invoices(self):
        """Get the actual tax amounts per tax based on the invoice lines
        associated with billing lines.
        Returns a dictionary where each key is a tax and the value is the total tax amount.
        """
        self.ensure_one()
        tax_summary = {}
        for line in self.billing_line_ids:
            invoice = line.move_id
            for tax_line in invoice.line_ids.filtered(
                lambda line: line.display_type == "tax"
                or (line.display_type == "rounding" and line.tax_repartition_line_id)
            ):
                tax = tax_line.tax_line_id
                tax_summary[tax] = tax_summary.get(tax, 0) + tax_line.credit
        return tax_summary

    def _group_invoice_lines_by_tax(self):
        """Group invoice lines by tax, summing the subtotals for each tax type.
        Returns a dictionary with tax as keys and subtotal as values.
        """
        self.ensure_one()
        grouped_lines = {}
        for line in self.billing_line_ids:
            invoice = line.move_id
            for inv_line in invoice.invoice_line_ids:
                for tax in inv_line.tax_ids:
                    if tax not in grouped_lines:
                        grouped_lines[tax] = inv_line.price_subtotal
                    else:
                        grouped_lines[tax] += inv_line.price_subtotal
        return grouped_lines

    def _get_calculated_tax_summary(self):
        """Calculate the tax amounts per tax based on the subtotal of each invoice line.
        Returns a dictionary where each key is a tax and the value is the expected tax amount.
        """
        self.ensure_one()
        calculated_tax_summary = {}
        tax_grouped_lines = self._group_invoice_lines_by_tax()
        for tax, subtotal in tax_grouped_lines.items():
            # Compute tax amount based on the subtotal and tax rates
            tax_amount = tax.compute_all(subtotal, self.currency_id)["taxes"][0][
                "amount"
            ]
            if self.env.company.tax_calculation_rounding_method == "round_globally":
                tax_amount = float_round(
                    tax_amount, precision_rounding=self.currency_id.rounding
                )
            calculated_tax_summary[tax] = tax_amount
        return calculated_tax_summary

    def _get_tax_differences(self, tax_summary, calculated_tax_summary):
        """Compare actual tax amounts from invoices with the expected tax amounts,
        and return the differences for each tax.
        """
        self.ensure_one()
        tax_differences = {}
        for tax, amount in tax_summary.items():
            summary_tax_amount = calculated_tax_summary.get(tax, 0)
            tax_diff = summary_tax_amount - amount
            if tax_diff != 0:
                tax_differences[tax] = tax_diff
        return tax_differences

    def _assign_tax_tags_to_entry(self, adjustment_entry, tax_account, tax_differences):
        """Assign the appropriate tax tags to the adjustment journal entry."""
        for line in adjustment_entry.line_ids.filtered(
            lambda l: l.account_id == tax_account and l.tax_ids
        ):
            for tax, _ in tax_differences.items():
                if f"Tax Adjustment for {tax.name}" in line.name:
                    line.tax_tag_ids = [
                        (6, 0, tax.invoice_repartition_line_ids[1].tag_ids.ids)
                    ]

    def validate_billing(self):
        res = super().validate_billing()
        # FIXME: Avoid using name
        tax_adjustment_tax = self.env["account.tax"].search(
            [("name", "=", "Adjustment")], limit=1
        )
        if not tax_adjustment_tax:
            tax_adjustment_tax = self.env["account.tax"].create(
                {
                    "name": "Adjustment",
                    "amount": 100.0,
                    "type_tax_use": "sale",
                    "price_include": True,
                }
            )
        for rec in self:
            invoice = self.billing_line_ids[0].move_id
            receivable_account = rec.partner_id.property_account_receivable_id
            tax_line = invoice.line_ids.filtered(
                lambda line: line.display_type == "tax"
                or (line.display_type == "rounding" and line.tax_repartition_line_id)
            )
            tax_account = tax_line[0].account_id
            tax_differences = rec._get_tax_differences(
                rec._get_tax_summary_from_invoices(), rec._get_calculated_tax_summary()
            )
            if not tax_differences:
                continue
            # journal = rec.tax_entry_journal_id
            adjustment_entry_vals = {
                "move_type": "entry",
                "date": rec.date,
                "line_ids": [],
            }
            credit = 0.0
            debit = 0.0
            for tax, difference in tax_differences.items():
                if difference != 0:
                    tax_debit_amount = abs(difference) if difference < 0 else 0
                    tax_credit_amount = abs(difference) if difference > 0 else 0
                    adjustment_entry_vals["line_ids"].append(
                        Command.create(
                            {
                                "account_id": tax_account.id,
                                "debit": tax_debit_amount,
                                "credit": tax_credit_amount,
                                "name": f"Tax Adjustment for {tax.name}",
                                "tax_ids": [(6, 0, tax_adjustment_tax.ids)],
                            },
                        )
                    )
                    debit += tax_credit_amount
                    credit += tax_debit_amount
            adjustment_entry_vals["line_ids"].append(
                Command.create(
                    {
                        "partner_id": rec.partner_id.id,
                        "account_id": receivable_account.id,
                        "debit": debit,
                        "credit": credit,
                        "name": "Tax Adjustment",
                    },
                )
            )
            rec.tax_adjustment_entry_id = self.env["account.move"].create(
                adjustment_entry_vals
            )
            rec._assign_tax_tags_to_entry(
                rec.tax_adjustment_entry_id, tax_account, tax_differences
            )
            rec.tax_adjustment_entry_id.line_ids.filtered(
                lambda line: not (
                    (line.account_id == tax_account and line.tax_ids)
                    or (line.account_id == receivable_account)
                )
            ).with_context(dynamic_unlink=True).unlink()
            rec.tax_adjustment_entry_id.action_post()
        return res

    def action_cancel(self):
        res = super().action_cancel()
        for rec in self:
            rec.tax_adjustment_entry_id.button_draft()
            rec.tax_adjustment_entry_id.button_cancel()
            rec.tax_adjustment_entry_id = False
        return res
