# Copyright 2024 Quartile
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "JP Summary Invoice",
    "version": "16.0.1.0.0",
    "category": "l10n",
    "author": "Quartile, Odoo Community Association (OCA)",
    "website": "https://www.quartile.co",
    "license": "AGPL-3",
    "depends": [
        "account_billing",
    ],
    "data": [
        "reports/report.xml",
        "reports/report_summary_invoice.xml",
        "views/account_account_tag_views.xml",
        "views/account_billing_views.xml",
    ],
    "installable": True,
}
