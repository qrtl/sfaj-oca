# Copyright 2025 Quartile
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    weight_address_src = fields.Float(default=1)
    weight_address_dest = fields.Float(default=1)
