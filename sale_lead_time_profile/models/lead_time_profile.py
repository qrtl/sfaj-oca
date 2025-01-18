# Copyright 2025 Quartile
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class LeadTimeProfile(models.Model):
    _name = "lead.time.profile"
    _description = "Lead Time Profile"
    _order = "country_id, state_id, partner_id, warehouse_id"

    warehouse_id = fields.Many2one("stock.warehouse")
    partner_id = fields.Many2one("res.partner", string="Delivery Address")
    state_id = fields.Many2one(
        "res.country.state", domain="[('country_id', '=?', country_id)]"
    )
    country_id = fields.Many2one(
        related="state_id.country_id", readonly=False, store=True, required=True
    )
    lead_time = fields.Float(required=True)

    def _get_score(self, warehouse, partner):
        self.ensure_one()
        score = 0
        if self.warehouse_id:
            if warehouse == self.warehouse_id:
                score += 1
            else:
                return -1
        if self.partner_id:
            if partner == self.partner_id:
                score += 3
            else:
                return -1
        elif self.state_id:
            if partner.state_id == self.state_id:
                score += 2
            else:
                return -1
        elif self.country_id:
            if partner.country_id == self.country_id:
                score += 1
            else:
                return -1
        return score
