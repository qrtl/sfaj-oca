# Copyright 2022-2024 Quartile Limited
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountTax(models.Model):
    _inherit = "account.tax"

    @api.model
    def _prepare_tax_totals(self, base_lines, currency, tax_lines=None):
        if self.env.company.need_tax_round_down:
            self = self.with_context(rounding_method="DOWN")
        return super()._prepare_tax_totals(base_lines, currency, tax_lines)

    def _compute_amount(
        self,
        base_amount,
        price_unit,
        quantity=1.0,
        product=None,
        partner=None,
        fixed_multiplicator=1,
    ):
        """Handle the case where round-down is required with the round_per_line setting.

        Due to how tax amount rounding is done inside the compute_all() method under the
        round_per_line setting (i.e. float_round() helper function is used instead of
        the round() method of the currency model), we want to apply the desired rounding
        using the model method beforehand.
        """
        amount = super()._compute_amount(
            base_amount, price_unit, quantity, product, partner, fixed_multiplicator
        )
        company = self.company_id
        if (
            company.need_tax_round_down
            and company.tax_calculation_rounding_method == "round_per_line"
            and self.amount_type == "percent"
        ):
            currency = self.env.context.get("currency") or company.currency
            amount = currency.with_context(rounding_method="DOWN").round(amount)
        return amount

    def compute_all(
        self,
        price_unit,
        currency=None,
        quantity=1.0,
        product=None,
        partner=None,
        is_refund=False,
        handle_price_include=True,
        include_caba_tags=False,
        fixed_multiplicator=1,
    ):
        # Just to pass the currency context used in _compute_amount()
        self = self.with_context(currency=currency)
        return super().compute_all(
            price_unit,
            currency,
            quantity,
            product,
            partner,
            is_refund,
            handle_price_include,
            include_caba_tags,
            fixed_multiplicator,
        )
