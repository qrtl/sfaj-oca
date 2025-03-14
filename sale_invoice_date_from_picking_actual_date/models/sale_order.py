# Copyright 2025 Quartile (https://www.quartile.co)
# Licence AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_picking_for_actual_date(self):
        self.ensure_one()
        complete_pickings = self.picking_ids.filtered(
            lambda p: p.state == "done"
        ).sorted("date_done")
        return complete_pickings[-1] if complete_pickings else False

    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()
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
