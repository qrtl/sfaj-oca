# Copyright 2024 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountBilling(models.Model):
    _inherit = "account.billing"

    amount_untaxed = fields.Monetary(compute="_compute_amount", store=True)
    total_amount = fields.Monetary(compute="_compute_amount", store=True)
    taxes = fields.Char(string="Tax", compute="_compute_amount", store=True)

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
