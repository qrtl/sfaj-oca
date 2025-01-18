# Copyright 2025 Quartile
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    weight_address_src = fields.Float(
        related="company_id.weight_address_src",
        readonly=False,
    )
    weight_address_dest = fields.Float(
        related="company_id.weight_address_dest",
        readonly=False,
    )

    def open_lead_time_profile_list(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Lead Time Profiles",
            "res_model": "lead.time.profile",
            "view_mode": "tree",
        }
