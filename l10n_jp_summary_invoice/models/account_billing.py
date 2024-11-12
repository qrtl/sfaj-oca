# Copyright 2024 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class AccountBilling(models.Model):
    _inherit = 'account.billing'

    tax_adjustment_entry_id = fields.Many2one("account.move")
    tax_entry_journal_id = fields.Many2one("account.journal", help="This journal will be used for tax adjustment journal entry.")

    def _get_tax_summary_from_invoices(self):
        """Get the actual tax amounts per tax based on the invoice lines associated with billing lines.
        Returns a dictionary where each key is a tax and the value is the total tax amount.
        """
        self.ensure_one()
        tax_summary = {}
        for line in self.billing_line_ids:
            invoice = line.move_id
            for tax_line in invoice.line_ids.filtered(lambda line: line.display_type == 'tax' or (line.display_type == 'rounding' and line.tax_repartition_line_id)):
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
            tax_amount = tax.compute_all(subtotal, self.currency_id)['taxes'][0]['amount']
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
        """Assign the appropriate tax tags to the adjustment journal entry.
        """
        for line in adjustment_entry.line_ids.filtered(lambda l: l.account_id == tax_account and l.tax_ids):
            for tax, _ in tax_differences.items():
                if f"Tax Adjustment for {tax.name}" in line.name:
                    line.tax_tag_ids = [(6, 0, tax.invoice_repartition_line_ids[1].tag_ids.ids)]

    def validate_billing(self):
        super().validate_billing()
        tax_adjustment_tax = self.env['account.tax'].search([('name', '=', 'Adjustment')], limit=1)
        if not tax_adjustment_tax:
            tax_adjustment_tax = self.env['account.tax'].create({
                'name': 'Adjustment',
                'amount': 100.0,
                'type_tax_use': 'sale',
                'price_include': True,
            })
        for rec in self:
            invoice = self.billing_line_ids[0].move_id if self.billing_line_ids else None
            receivable_line = invoice.line_ids.filtered(lambda line: line.account_id.account_type == 'asset_receivable')
            receivable_account = receivable_line[0].account_id if receivable_line else None
            tax_line = invoice.line_ids.filtered(lambda line: line.tax_line_id and line.account_id.account_type == 'liability_current')
            tax_account = tax_line[0].account_id
            tax_differences = rec._get_tax_differences(
                rec._get_tax_summary_from_invoices(),
                rec._get_calculated_tax_summary()
            )
            if not tax_differences:
                continue
            journal = rec.tax_entry_journal_id
            adjustment_entry_vals = {
                'journal_id': journal.id,
                'date': rec.date,
                'line_ids': [],
            }
            credit = 0.0
            debit = 0.0
            for tax, difference in tax_differences.items():
                if difference != 0:
                    adjustment_entry_vals['line_ids'].append((0, 0, {
                        'account_id': tax_account.id,
                        'credit': abs(difference) if difference > 0 else 0,
                        'debit': abs(difference) if difference < 0 else 0,
                        'name': f"Tax Adjustment for {tax.name}",
                        'tax_ids': [(6, 0, tax_adjustment_tax.ids)],
                    }))
                    debit += abs(difference) if difference > 0 else 0
                    credit += abs(difference) if difference < 0 else 0
            adjustment_entry_vals['line_ids'].append((0, 0, {
                'account_id': receivable_account.id,
                'debit': debit,
                'credit': credit,
                'name': 'Tax Adjustment'
            }))
            rec.tax_adjustment_entry_id = self.env['account.move'].create(adjustment_entry_vals)
            rec._assign_tax_tags_to_entry(rec.tax_adjustment_entry_id, tax_account, tax_differences)
            rec.tax_adjustment_entry_id.line_ids.filtered(
                lambda line: not (
                    (line.account_id == tax_account and line.tax_ids) or
                    (line.account_id == receivable_account)
                )
            ).with_context(dynamic_unlink=True).unlink()
            rec.tax_adjustment_entry_id.action_post()
    
    def action_cancel(self):
        super().action_cancel()
        for rec in self:
            rec.tax_adjustment_entry_id.button_draft()
            rec.tax_adjustment_entry_id.button_cancel()
            rec.tax_adjustment_entry_id = False
