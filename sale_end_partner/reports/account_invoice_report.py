# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    end_partner_id = fields.Many2one("res.partner", string="End Customer")

    def _select(self):
        select_str = super()._select()
        select_str += """
            , move.end_partner_id as end_partner_id
            """
        return select_str
