# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    summary_invoice_remark = fields.Html(
        related="company_id.summary_invoice_remark", readonly=False
    )
    show_sale_order_number = fields.Boolean(
        related="company_id.show_sale_order_number", readonly=False
    )
