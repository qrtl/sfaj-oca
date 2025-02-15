# Copyright 2022-2024 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from contextlib import contextmanager

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    @contextmanager
    def _sync_dynamic_line(
        self,
        existing_key_fname,
        needed_vals_fname,
        needed_dirty_fname,
        line_type,
        container,
    ):
        if line_type == "tax" and self.env.company.need_tax_round_down:
            self = self.with_context(rounding_method="DOWN")
        with super()._sync_dynamic_line(
            existing_key_fname,
            needed_vals_fname,
            needed_dirty_fname,
            line_type,
            container,
        ) as ret:
            yield ret
