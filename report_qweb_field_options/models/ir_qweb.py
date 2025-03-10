# Copyright 2024-2025 Quartile (https://www.quartile.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class IrQweb(models.AbstractModel):
    _inherit = "ir.qweb"

    @api.model
    def _get_field(
        self, record, field_name, expression, tagName, field_options, values
    ):
        if values.get("report_type") == "pdf":
            options_recs = self.env["qweb.field.options"].search(
                [("res_model_name", "=", record._name), ("field_name", "=", field_name)]
            )
            if options_recs:
                options_rec = max(
                    options_recs, default=None, key=lambda r: r._get_score(record)
                )
                field_options = options_rec._update_field_options(record, field_options)
        return super()._get_field(
            record, field_name, expression, tagName, field_options, values
        )
