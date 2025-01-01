# Copyright 2022 Quartile
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, tools


class Currency(models.Model):
    _inherit = "res.currency"

    def round(self, amount):
        self.ensure_one()
        rounding_method = self.env.context.get("rounding_method")
        if rounding_method:
            return tools.float_round(
                amount,
                precision_rounding=self.rounding,
                rounding_method=rounding_method,
            )
        return super().round(amount)
