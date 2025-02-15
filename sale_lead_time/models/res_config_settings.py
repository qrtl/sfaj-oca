# Copyright 2025 Quartile
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    factor_warehouse = fields.Float(
        related="company_id.factor_warehouse", readonly=False
    )
    factor_country = fields.Float(related="company_id.factor_country", readonly=False)
    factor_state = fields.Float(related="company_id.factor_state", readonly=False)
    factor_partner = fields.Float(related="company_id.factor_partner", readonly=False)

    def open_lead_time_profile_list(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Lead Time Profiles",
            "res_model": "lead.time.profile",
            "view_mode": "tree",
        }
