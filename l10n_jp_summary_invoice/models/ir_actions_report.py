# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class Report(models.Model):
    _inherit = "ir.actions.report"

    def _get_remit_to_bank(self, record):
        if record._name == "account.billing":
            return record.remit_to_bank_id
        return super()._get_remit_to_bank(record)
