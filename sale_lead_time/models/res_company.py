# Copyright 2025 Quartile
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    factor_warehouse = fields.Float(default=1.0)
    factor_country = fields.Float(default=1.0)
    factor_state = fields.Float(default=1.0)
    factor_partner = fields.Float(default=1.0)
