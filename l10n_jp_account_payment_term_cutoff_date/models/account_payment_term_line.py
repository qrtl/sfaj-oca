from dateutil.relativedelta import relativedelta

from odoo import fields, models


class AccountPaymentTermLine(models.Model):
    _inherit = "account.payment.term.line"

    cutoff_date = fields.Integer(
        help="If you set this to 20,"
        "invoices dated on the 21st or later will have"
        "their due date shifted by one additional month.",
    )

    def _get_due_date(self, date_ref):
        due_date = super()._get_due_date(date_ref)
        if self.cutoff_date and date_ref:
            date_dt = fields.Date.to_date(date_ref)
            if date_dt.day > self.cutoff_date:
                due_date += relativedelta(months=1)
        return due_date
