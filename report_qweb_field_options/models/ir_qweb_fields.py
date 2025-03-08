# Copyright 2024 Quartile Limited (https://www.quartile.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class FloatConverter(models.AbstractModel):
    _inherit = "ir.qweb.field.float"

    @api.model
    def record_to_html(self, record, field_name, options):
        if "precision" not in options and "decimal_precision" not in options:
            options_rec = self.env["qweb.field.options"]._get_options_rec(
                record, field_name
            )
            if options_rec:
                options = dict(options, precision=options_rec.digits)
        return super().record_to_html(record, field_name, options)
