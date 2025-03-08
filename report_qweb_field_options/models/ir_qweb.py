# Copyright 2024-2025 Quartile (https://www.quartile.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import ast
import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class IrQweb(models.AbstractModel):
    _inherit = "ir.qweb"

    @api.model
    def _get_field(
        self, record, field_name, expression, tagName, field_options, values
    ):
        report_type = values.get("report_type")
        if not report_type or report_type != "pdf":
            return super()._get_field(
                record, field_name, expression, tagName, field_options, values
            )
        options_rec = self.env["qweb.field.options"]._get_options_rec(
            record, field_name
        )
        if options_rec and options_rec.field_options:
            try:
                extra_options = ast.literal_eval(options_rec.field_options)
                if extra_options.get("widget") == "monetary":
                    extra_options["display_currency"] = (
                        options_rec.currency_id
                        or hasattr(record, "company_id")
                        and record.company_id.currency_id
                        or self.env.company.currency_id
                    )
                field_options.update(extra_options)
            except Exception as e:
                _logger.error(
                    "Failed to parse field options as a dictionary: "
                    f"{options_rec.field_options}. Error: {e}"
                )
        return super()._get_field(
            record, field_name, expression, tagName, field_options, values
        )
