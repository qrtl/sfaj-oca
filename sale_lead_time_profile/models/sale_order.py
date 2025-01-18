# Copyright 2025 Quartile
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    delivery_lead_time = fields.Float(
        compute="_compute_delivery_lead_time",
        store=True,
        readonly=False,
        help="Number of days expected for delivery from the warehouse to the delivery address.",
    )

    @api.depends("warehouse_id", "partner_shipping_id")
    def _compute_delivery_lead_time(self):
        for rec in self:
            rec.delivery_lead_time = 0.0
            if not rec.partner_shipping_id:
                continue
            profiles = self.env["lead.time.profile"].search(
                [
                    "|",
                    ("warehouse_id", "=", rec.warehouse_id.id),
                    ("warehouse_id", "=", False),
                ]
            )
            if not profiles:
                continue
            profile_scores = {
                profile: profile._get_score(rec.warehouse_id, rec.partner_shipping_id)
                for profile in profiles
            }
            best_profile = max(profile_scores, key=profile_scores.get, default=None)
            rec.delivery_lead_time = (
                best_profile.lead_time if profile_scores[best_profile] > 0 else 0.00
            )
