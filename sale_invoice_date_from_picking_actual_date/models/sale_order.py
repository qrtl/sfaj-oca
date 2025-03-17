# Copyright 2025 Quartile (https://www.quartile.co)
# Licence AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_picking_for_actual_date(self):
        self.ensure_one()
        return self.picking_ids.filtered(lambda p: p.state == "done").sorted(
            key=lambda p: p.date_done, reverse=True
        )[:1]

    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()
        if not self.company_id.use_picking_actual_date_for_invoice:
            return invoice_vals
        picking = self._get_picking_for_actual_date()
        if picking:
            if picking.actual_date:
                invoice_vals["invoice_date"] = picking.actual_date
            else:
                invoice_vals["invoice_date"] = fields.Datetime.context_timestamp(
                    self.with_context(tz=self.company_id.partner_id.tz),
                    picking.date_done,
                )
        return invoice_vals
