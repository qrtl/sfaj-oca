# Copyright 2024-2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "JP Summary Invoice",
    "version": "16.0.1.0.0",
    "category": "l10n",
    "author": "Quartile, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-japan",
    "license": "AGPL-3",
    "depends": ["account_billing", "report_alternative_layout"],
    "data": [
        "reports/report.xml",
        "reports/report_summary_invoice.xml",
        "views/account_billing_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
}
