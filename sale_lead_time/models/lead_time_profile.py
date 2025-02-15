# Copyright 2025 Quartile
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class LeadTimeProfile(models.Model):
    _name = "lead.time.profile"
    _description = "Lead Time Profile"
    _order = "country_id, state_id, partner_id, warehouse_id"

    warehouse_id = fields.Many2one(
        "stock.warehouse", help="Matched against the warehouse of the sales order."
    )
    partner_id = fields.Many2one(
        "res.partner", help="Matched against the delivery address of the sales order."
    )
    state_id = fields.Many2one(
        "res.country.state",
        domain="[('country_id', '=?', country_id)]",
        help="Matched against the state of the delivery address of the sales order.",
    )
    country_id = fields.Many2one(
        "res.country",
        help="Matched against the country of the delivery address of the sales order.",
    )
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
    lead_time = fields.Float(string="Lead Time (Days)", required=True)

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        for rec in self:
            if rec.partner_id:
                rec.state_id = rec.partner_id.state_id

    @api.onchange("state_id")
    def _onchange_state_id(self):
        for rec in self:
            if rec.partner_id.state_id != rec.state_id:
                rec.partner_id = False
            rec.country_id = rec.state_id.country_id

    @api.onchange("country_id")
    def _onchange_country_id(self):
        for rec in self:
            if rec.state_id.country_id != rec.country_id:
                rec.state_id = False
            if rec.partner_id.country_id != rec.country_id:
                rec.partner_id = False

    def _get_score(self, **kwargs):
        """Return a matching score for this lead time profile.

        The method scores each relevant match (warehouse/country/state/partner)
        based on factors defined in the company. For example, if the partner matches,
        the score is increased by the factor_partner. If any mismatch is found, it
        immediately returns -1.

        :param kwargs: Dictionary containing 'warehouse' and 'partner'.
        :return: A float representing the total match score if no mismatch is found,
            or -1 if any mismatch is found.
        """
        self.ensure_one()
        score = 0
        partner = kwargs.get("partner")
        warehouse = kwargs.get("warehouse")
        company = self.company_id
        if self.partner_id:
            if partner == self.partner_id:
                score += company.factor_partner
            else:
                return -1
        if self.state_id:
            if partner.state_id == self.state_id:
                score += company.factor_state
            else:
                return -1
        if self.country_id:
            if partner.country_id == self.country_id:
                score += company.factor_country
            else:
                return -1
        if self.warehouse_id:
            if warehouse == self.warehouse_id:
                score += company.factor_warehouse
            else:
                return -1
        return score
