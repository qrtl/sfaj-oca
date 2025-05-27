# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields


class ReportPaperformat(models.Model):
    _inherit = "report.paperformat"

    show_address_in_header = fields.Boolean(
        help="If selected, the report header will be shown on every page of the "
        "report output.",
    )
