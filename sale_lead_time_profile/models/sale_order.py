# Copyright 2025 Quartile
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.osv import expression


class SaleOrder(models.Model):
    _inherit = "sale.order"

    delivery_lead_time = fields.Float(
        compute="_compute_delivery_lead_time",
        store=True,
        readonly=False,
        help="Number of days expected for delivery from the warehouse to the delivery address.",
    )

    def _get_address_src_domain(self):
        self.ensure_one()
        return [
            "|",
            ("warehouse_id", "=", self.warehouse_id.id),
            ("warehouse_id", "=", False),
        ]

    def _get_address_dest_domain(self):
        self.ensure_one()
        partner = self.partner_shipping_id
        partner_domain = [("partner_id", "=", partner.id)]
        state_domain = [
            ("partner_id", "=", False),
            ("state_id", "=", partner.state_id.id),
        ]
        country_domain = [
            ("partner_id", "=", False),
            ("state_id", "=", False),
            ("country_id", "=", partner.country_id.id),
        ]
        no_address_domain = [
            ("partner_id", "=", False),
            ("state_id", "=", False),
            ("country_id", "=", False),
        ]
        return expression.OR(
            [partner_domain, state_domain, country_domain, no_address_domain]
        )

    @api.depends("warehouse_id", "partner_shipping_id")
    def _compute_delivery_lead_time(self):
        for rec in self:
            rec.delivery_lead_time = 0.0
            if not rec.partner_shipping_id:
                continue
            address_src_domain = rec._get_address_src_domain()
            address_dest_domain = rec._get_address_dest_domain()
            domain = expression.AND([address_src_domain, address_dest_domain])
            profiles = self.env["lead.time.profile"].search(domain)
            if not profiles:
                continue
            profile_scores = {
                profile: profile._get_score(
                    **{
                        "warehouse": rec.warehouse_id,
                        "partner": rec.partner_shipping_id,
                    }
                )
                for profile in profiles
            }
            best_profile = max(profile_scores, key=profile_scores.get, default=None)
            rec.delivery_lead_time = (
                best_profile.lead_time if profile_scores[best_profile] > 0 else 0.00
            )
