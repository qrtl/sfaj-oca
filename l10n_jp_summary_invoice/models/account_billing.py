# Copyright 2024 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


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
        invoice = self.billing_line_ids[0].move_id if self.billing_line_ids else None
        # receivable_line = invoice.line_ids.filtered(lambda line: line.account_id.account_type == 'asset_receivable')
        # receivable_account = receivable_line[0].account_id if receivable_line else None
        tax_line = invoice.line_ids.filtered(lambda line: line.tax_line_id and line.account_id.account_type == 'liability_current')
        tax_account = tax_line[0].account_id if tax_line else None
        tax_adjustment_tax = self.env['account.tax'].search([('name', '=', 'Tax Adj')], limit=1)
        if not tax_adjustment_tax:
            tax_adjustment_tax = self.env['account.tax'].create({
                'name': 'Tax Adjustment',
                'amount': 100.0,
                'type_tax_use': 'sale',
                'price_include': True,
            })
        for rec in self:
            if rec.tax_difference != 0:
                invoice_vals = {
                    'move_type': 'out_invoice',
                    'partner_id': rec.partner_id.id,
                    'invoice_date': rec.date,
                    'invoice_line_ids': [
                        (0, 0, {
                            'name': 'Tax Adjustment Line',
                            'quantity': 1,
                            'price_unit': abs(rec.tax_difference),
                            'account_id': tax_account.id,
                            'tax_ids': [(6, 0, [tax_adjustment_tax.id])],
                        }),
                    ],
                }
                invoice = self.env['account.move'].create(invoice_vals)
                invoice.action_post()
                rec.tax_adjustment_entry_id = invoice.id
        
    def action_cancel(self):
        super().action_cancel()
        for rec in self:
            rec.tax_adjustment_entry_id.button_draft()
            rec.tax_adjustment_entry_id.button_cancel()
            rec.tax_adjustment_entry_id = False