# Copyright 2024 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class AccountAccounttag(models.Model):
    _inherit = 'account.account.tag'

    is_use_in_tax_adjustment = fields.Boolean(help="If enabled, this will be used as the tax grid in adjustment tax records.")
