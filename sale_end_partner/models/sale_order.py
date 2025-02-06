# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    end_partner_id = fields.Many2one(
        "res.partner",
        string="End Customer",
        tracking=True,
        states={state: [("readonly", True)] for state in {"sale", "done", "cancel"}},
        domain="[('type', '!=', 'private'), ('company_id', 'in', (False, company_id))]",
    )

    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()
        invoice_vals["end_partner_id"] = self.end_partner_id.id
        return invoice_vals
