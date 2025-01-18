# Copyright 2025 Quartile
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Sale Lead Time Profile",
    "version": "16.0.1.0.0",
    "author": "Quartile, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/sale-workflow",
    "license": "AGPL-3",
    "depends": ["sale_stock"],
    "data": [
        "security/lead_time_profile_security.xml",
        "security/ir.model.access.csv",
        "views/lead_time_profile_views.xml",
        "views/res_config_settings_view.xml",
        "views/sale_order_views.xml",
    ],
    "installable": True,
}
