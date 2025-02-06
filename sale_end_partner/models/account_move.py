# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    end_partner_id = fields.Many2one(
        "res.partner",
        string="End Customer",
        readonly=True,
        tracking=True,
        states={"draft": [("readonly", False)]},
        ondelete="restrict",
        check_company=True,
    )
