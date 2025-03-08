# Copyright 2024-2025 Quartile (https://www.quartile.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import ast

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class QwebFieldOptions(models.Model):
    _name = "qweb.field.options"
    _description = "Qweb Field Options"
    _order = "res_model_id, field_id"

    res_model_id = fields.Many2one(
        "ir.model", string="Model", ondelete="cascade", required=True
    )
    res_model_name = fields.Char("Model Name", related="res_model_id.model", store=True)
    field_id = fields.Many2one(
        "ir.model.fields",
        domain="[('model_id', '=', res_model_id)]",
        string="Field",
        ondelete="cascade",
        required=True,
    )
    field_type = fields.Selection(related="field_id.ttype", store=True)
    field_name = fields.Char("Field Name", related="field_id.name", store=True)
    uom_id = fields.Many2one("uom.uom", string="UoM", ondelete="cascade")
    uom_field_id = fields.Many2one(
        "ir.model.fields",
        domain="[('model_id', '=', res_model_id), ('relation', '=', 'uom.uom')]",
        string="UoM Field",
        ondelete="cascade",
    )
    currency_id = fields.Many2one("res.currency", string="Currency", ondelete="cascade")
    currency_field_id = fields.Many2one(
        "ir.model.fields",
        domain="[('model_id', '=', res_model_id), ('relation', '=', 'res.currency')]",
        string="Currency Field",
        ondelete="cascade",
    )
    field_options = fields.Char(
        "Options",
        help="A string representation of a dictionary to specify field formatting "
        "options. Examples:\n"
        "{'widget': 'date'}\n"
        "{'widget': 'monetary'}\n"
        "{'widget': 'contact', 'fields': ['name', 'phone']}.",
    )
    digits = fields.Integer()
    company_id = fields.Many2one("res.company", string="Company")

    @api.constrains("field_options")
    def _check_field_options_format(self):
        for rec in self:
            field_options = False
            try:
                field_options = ast.literal_eval(rec.field_options)
            except Exception as e:
                raise ValidationError(
                    _(
                        "Invalid string for the Options field: %(field_options)s.\n"
                        "Error: %(error)s"
                    )
                    % {"field_options": rec.field_options, "error": e}
                ) from e
            if not isinstance(field_options, dict):
                raise ValidationError(
                    _("Options must be a dictionary, but got %s") % type(field_options)
                )

    def _get_score(self, record):
        self.ensure_one()
        score = 1
        if self.company_id:
            if record.company_id == self.company_id:
                score += 1
            else:
                return -1
        if self.uom_id:
            if record[self.uom_field_id.sudo().name] == self.uom_id:
                score += 1
            else:
                return -1
        if self.currency_id:
            if record[self.currency_field_id.sudo().name] == self.currency_id:
                score += 1
            else:
                return -1
        return score

    @api.model
    def _get_options_rec(self, record, field_name):
        options_recs = self.env["qweb.field.options"].search(
            [("res_model_name", "=", record._name), ("field_name", "=", field_name)]
        )
        return max(options_recs, default=None, key=lambda r: r._get_score(record))
