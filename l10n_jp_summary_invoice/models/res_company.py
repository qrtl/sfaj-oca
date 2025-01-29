# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    summary_invoice_remark = fields.Html(
        translate=True,
        help="Content here will be displayed in the summary invoice report.",
    )
