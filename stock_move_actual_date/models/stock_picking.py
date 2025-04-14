# Copyright 2024 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class StockPicking(models.Model):
    _name = "stock.picking"
    _inherit = ["stock.picking", "actual.date.mixin"]

    def _get_trigger_field_names_for_actual_date_source(self):
        return ["date_done", "move_ids"]

    def _get_stock_moves(self):
        self.ensure_one()
        return self.move_ids
