# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SaleReport(models.Model):
    _inherit = "sale.report"

    end_partner_id = fields.Many2one("res.partner", string="End Customer")

    def _select_additional_fields(self):
        res = super()._select_additional_fields()
        res["end_partner_id"] = "s.end_partner_id"
        return res

    def _group_by_sale(self):
        res = super()._group_by_sale()
        res += """,
            s.end_partner_id"""
        return res
