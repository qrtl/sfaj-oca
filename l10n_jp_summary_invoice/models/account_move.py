# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    is_not_for_billing = fields.Boolean(
        help="If selected, the invoice is excluded from the billing process.",
    )

    # TODO: Propose to move this to account_billing?
    def button_draft(self):
        for rec in self:
            if rec.billing_ids.filtered(lambda x: x.state != "cancel"):
                raise UserError(
                    _("You cannot reset to draft an invoice that has been billed.")
                )
        return super().button_draft()
