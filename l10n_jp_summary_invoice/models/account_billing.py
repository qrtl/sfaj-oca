# Copyright 2024 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api
from itertools import groupby
from operator import itemgetter


class AccountBilling(models.Model):
    _inherit = 'account.billing'

    summary_invoice_amount_tax = fields.Monetary(
        compute="_compute_amount_tax",
        store=True,
    )
    invoice_tax_sum = fields.Monetary(
        string="Invoices Tax Sum",
        compute="_compute_amount_tax",
    )
    tax_difference = fields.Monetary(
        string="Tax Difference",
        compute="_compute_tax_difference",
        store=True,
    )
    tax_adjustment_entry_id = fields.Many2one("account.move")
    tax_entry_journal_id = fields.Many2one("account.journal", help="This journal will be used for tax adjustment journal entry.")

    @api.depends('billing_line_ids.move_id')
    def _compute_amount_tax(self):
        for billing in self:
            line_data = []
            tax_sum = 0.0
            for line in billing.billing_line_ids:
                invoice = line.move_id
                if invoice:
                    tax_sum += line.move_id.amount_tax
                    for inv_line in invoice.invoice_line_ids:
                        for tax in inv_line.tax_ids:
                            line_data.append((inv_line.price_subtotal, tax))
            billing.invoice_tax_sum = tax_sum
            # Sort and group by tax
            invoice_tax_total = 0.0
            grouped_lines = {}
            for subtotal, tax in line_data:
                if tax not in grouped_lines:
                    grouped_lines[tax] = 0
                grouped_lines[tax] += subtotal
            for tax, subtotal_sum in grouped_lines.items():
                invoice_tax_total += tax.compute_all(subtotal_sum, billing.currency_id)['taxes'][0]['amount']
            billing.summary_invoice_amount_tax = invoice_tax_total

    @api.depends('summary_invoice_amount_tax', 'invoice_tax_sum')
    def _compute_tax_difference(self):
        for billing in self:
            billing.tax_difference = abs(billing.summary_invoice_amount_tax - billing.invoice_tax_sum)

    def validate_billing(self):
        super().validate_billing()
        for rec in self:
            if rec.tax_difference != 0:
                invoice = self.billing_line_ids[0].move_id if self.billing_line_ids else None
                receivable_line = invoice.line_ids.filtered(lambda line: line.account_id.account_type == 'asset_receivable')
                receivable_account = receivable_line[0].account_id if receivable_line else None
                tax_line = invoice.line_ids.filtered(lambda line: line.tax_line_id and line.account_id.account_type == 'liability_current')
                tax_account = tax_line[0].account_id if tax_line else None
                adjustment_entry_vals = {
                    'journal_id': self.tax_entry_journal_id.id,
                    'date': rec.date,
                    'line_ids': [
                        (0, 0, {
                            'account_id': receivable_account.id,
                            'debit': rec.tax_difference if rec.tax_difference > 0 else 0,
                            'credit': -rec.tax_difference if rec.tax_difference < 0 else 0,
                            'name': 'Tax Adjustment',
                        }),
                        (0, 0, {
                            'account_id': tax_account.id,
                            'debit': -rec.tax_difference if rec.tax_difference < 0 else 0,
                            'credit': rec.tax_difference if rec.tax_difference > 0 else 0,
                            'name': 'Tax Adjustment',
                        })
                    ]
                }
                # Create the journal entry
                adjustment_entry = self.env['account.move'].create(adjustment_entry_vals)
                # Optionally link the adjustment entry to the billing record
                rec.tax_adjustment_entry_id = adjustment_entry.id
