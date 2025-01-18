# Copyright 2025 Quartile
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class LeadTimeProfile(models.Model):
    _name = "lead.time.profile"
    _description = "Lead Time Profile"
    _order = "country_id, state_id, partner_id, warehouse_id"

    warehouse_id = fields.Many2one("stock.warehouse", string="Warehouse (Src)")
    partner_id = fields.Many2one("res.partner", string="Partner (Dest)")
    state_id = fields.Many2one(
        "res.country.state",
        string="State (Dest)",
        domain="[('country_id', '=?', country_id)]",
    )
    country_id = fields.Many2one("res.country", string="Country (Dest)")
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
    lead_time = fields.Float(string="Lead Time (Days)", required=True)

    @api.onchange("partner_id")
    def _onchagnge_partner_id(self):
        for rec in self:
            if rec.partner_id:
                rec.state_id = rec.partner_id.state_id

    @api.onchange("state_id")
    def _onchagnge_state_id(self):
        for rec in self:
            if rec.partner_id.state_id != rec.state_id:
                rec.partner_id = False
            rec.country_id = rec.state_id.country_id

    @api.onchange("country_id")
    def _onchagnge_country_id(self):
        for rec in self:
            if rec.state_id.country_id != rec.country_id:
                rec.state_id = False
            if rec.partner_id.country_id != rec.country_id:
                rec.partner_id = False

    def _get_score(self, **kwargs):
        """Return a matching score for this lead time profile.

        The method scores each relevant match (warehouse, partner, state, country)
        based on the Source Address Weight and Destination Address Weight defined in the
        company. If any mismatch is found, it immediately returns -1.

        Specifically:
        - If the warehouse (source address) matches, Source Address Weight is added.
        - For the partner, state, and country matches, Destination Address Weight is
        divided into three equal parts, each added if there's a match.
        - Any mismatch in warehouse, partner, state, or country returns -1 at once.

        :param kwargs: Dictionary containing 'warehouse' and 'partner'.
        :return: A float representing the total match score if not mismatch is found,
            or -1 if any mismatch is found.
        """
        self.ensure_one()
        score = 0
        warehouse = kwargs.get("warehouse")
        partner = kwargs.get("partner")
        weight_address_src = self.company_id.weight_address_src
        # We split the weight among partner, state and country
        weight_address_dest = self.company_id.weight_address_dest / 3
        # Add score based on the source address
        if self.warehouse_id:
            if warehouse == self.warehouse_id:
                score += weight_address_src
            else:
                return -1
        # Add score based on the destination address (partner/state/country)
        if self.partner_id:
            if partner == self.partner_id:
                score += weight_address_dest
            else:
                return -1
        if self.state_id:
            if partner.state_id == self.state_id:
                score += weight_address_dest
            else:
                return -1
        if self.country_id:
            if partner.country_id == self.country_id:
                score += weight_address_dest
            else:
                return -1
        return score
