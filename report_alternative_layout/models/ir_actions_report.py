# Copyright 2024 Quartile
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class Report(models.Model):
    _inherit = "ir.actions.report"

    apply_alternative_layout = fields.Boolean(
        help="If selected, the alternative layout will be applied in the printed "
        "report.",
    )
    show_commercial_partner = fields.Boolean(
        help="If selected, the commercial partner of the document partner will show "
        "in the report output (instead of the document partner)."
    )

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        report = self._get_report(report_ref)
        if report.apply_alternative_layout:
            self = self.with_context(apply_alternative_layout=True)
        return super()._render_qweb_pdf(report_ref, res_ids, data)

    def _get_partner(self, xmlid, partner):
        report = self._get_report_from_name(xmlid)
        if report.show_commercial_partner:
            return partner.commercial_partner_id
        return partner
