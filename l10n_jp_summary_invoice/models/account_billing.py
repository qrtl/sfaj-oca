# Copyright 2024 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _
from odoo.exceptions import UserError


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
            tax_sum = sum(line.move_id.amount_tax for line in billing.billing_line_ids if line.move_id)
            billing.invoice_tax_sum = tax_sum
            grouped_lines = {}
            for line in billing.billing_line_ids:
                invoice = line.move_id
                for inv_line in invoice.invoice_line_ids:
                    for tax in inv_line.tax_ids:
                        if tax not in grouped_lines:
                            grouped_lines[tax] = inv_line.price_subtotal
                            continue
                        grouped_lines[tax] += inv_line.price_subtotal
            billing.summary_invoice_amount_tax = sum(
                tax.compute_all(subtotal, billing.currency_id)['taxes'][0]['amount']
                for tax, subtotal in grouped_lines.items()
            )

    @api.depends('summary_invoice_amount_tax', 'invoice_tax_sum')
    def _compute_tax_difference(self):
        for billing in self:
            billing.tax_difference = billing.summary_invoice_amount_tax - billing.invoice_tax_sum

    def validate_billing(self):
        super().validate_billing()
        invoice = self.billing_line_ids[0].move_id if self.billing_line_ids else None
        receivable_line = invoice.line_ids.filtered(lambda line: line.account_id.account_type == 'asset_receivable')
        receivable_account = receivable_line[0].account_id if receivable_line else None
        tax_line = invoice.line_ids.filtered(lambda line: line.tax_line_id and line.account_id.account_type == 'liability_current')
        tax_account = tax_line[0].account_id if tax_line else None
        tag_ids = self.env['account.account.tag'].search([('is_use_in_tax_adjustment', '=', True)])
        if not tag_ids:
            raise UserError(_("There are no tax grids for the adjustment tax."))
        tax_adjustment_tax = self.env['account.tax'].search([('name', '=', 'Adjustment')], limit=1)
        if not tax_adjustment_tax:
            tax_adjustment_tax = self.env['account.tax'].create({
                'name': 'Adjustment',
                'amount': 100.0,
                'type_tax_use': 'sale',
                'price_include': True,
            })
            tax_adjustment_tax.invoice_repartition_line_ids[0].tag_ids = [(6, 0, tag_ids.ids)]
            tax_adjustment_tax.refund_repartition_line_ids[0].tag_ids = [(6, 0, tag_ids.ids)]
        for rec in self:
            if rec.tax_difference != 0:
                adjustment_entry_vals = {
                    'journal_id': self.tax_entry_journal_id.id,
                    'date': rec.date,
                    'line_ids': [
                        (0, 0, {
                            'account_id': tax_account.id,
                            'debit': 0.0,
                            'credit': rec.tax_difference,
                            'tax_ids': [(6, 0, tax_adjustment_tax.ids)],
                            'name': 'Tax Adjustment',
                        }),
                        (0, 0, {
                            'account_id': receivable_account.id,
                            'debit': rec.tax_difference,
                            'credit': 0.0,
                            'name': 'Tax Adjustment',
                        })
                    ]
                }
                adjustment_entry = self.env['account.move'].create(adjustment_entry_vals)
                adjustment_entry.line_ids.filtered(
                    lambda line: not (
                        (line.account_id == tax_account and line.tax_ids) or
                        (line.account_id == receivable_account)
                    )
                ).with_context(dynamic_unlink=True).unlink()
                adjustment_entry.action_post()
                rec.tax_adjustment_entry_id = adjustment_entry.id
        
    def action_cancel(self):
        super().action_cancel()
        for rec in self:
            rec.tax_adjustment_entry_id.button_draft()
            rec.tax_adjustment_entry_id.button_cancel()
            rec.tax_adjustment_entry_id = False
