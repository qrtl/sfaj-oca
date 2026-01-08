# Copyright 2024 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
import re

from lxml import html
from markupsafe import Markup

from odoo import api, models
from odoo.tools.profiler import QwebTracker
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class IrQWeb(models.AbstractModel):
    _inherit = "ir.qweb"

    def _apply_global_mappings(self, html_str, mappings):
        """Apply mappings without domain on the whole HTML string."""
        for mapping in mappings:
            html_str = html_str.replace(
                mapping.content_from,
                mapping.content_to or "",
            )
        return html_str

    def _record_matches_domain(self, model_name, res_id, domain_str):
        """Check if record (model_name, res_id) matches the given domain."""
        if not domain_str:
            return True
        try:
            dom = safe_eval(domain_str)
        except Exception:
            _logger.warning(
                "Invalid domain on template.content.mapping for %s,%s: %s",
                model_name,
                res_id,
                domain_str,
            )
            return False
        return bool(self.env[model_name].search_count([("id", "=", res_id)] + dom))

    def _apply_domain_mappings_single_record(
        self,
        html_str,
        model_name,
        res_id,
        domain_mappings,
    ):
        """When exactly one record is rendered, domain mappings can be applied
        on the entire HTML for that render (header/footer + body).
        """
        for mapping in domain_mappings:
            if mapping.report_model and mapping.report_model != model_name:
                continue
            if not self._record_matches_domain(model_name, res_id, mapping.domain):
                continue
            html_str = html_str.replace(
                mapping.content_from,
                mapping.content_to or "",
            )
        return html_str

    def _apply_domain_mappings_on_articles(self, root, domain_mappings):
        """Apply domain mappings only inside each article block when multiple
        records are rendered in one HTML.
        """
        articles = root.xpath(
            '//div[contains(@class, "article")' " and @data-oe-model and @data-oe-id]"
        )
        if not articles:
            return
        for article in articles:
            model_name = article.get("data-oe-model")
            res_id = int(article.get("data-oe-id"))
            applicable = [
                m
                for m in domain_mappings
                if not m.report_model or m.report_model == model_name
            ]
            if not applicable:
                continue
            record = self.env[model_name].browse(res_id)
            if not record.exists():
                continue
            article_html = html.tostring(article, encoding="unicode")
            new_article_html = article_html
            for mapping in applicable:
                if not self._record_matches_domain(
                    model_name,
                    res_id,
                    mapping.domain,
                ):
                    continue
                new_article_html = new_article_html.replace(
                    mapping.content_from,
                    mapping.content_to or "",
                )
            if new_article_html != article_html:
                try:
                    new_node = html.fromstring(new_article_html)
                    article.getparent().replace(article, new_node)
                except Exception:
                    _logger.exception(
                        "Failed to replace article HTML for record %s,%s",
                        model_name,
                        res_id,
                    )

    @QwebTracker.wrap_render
    @api.model
    def _render(self, template, values=None, **options):
        result = super()._render(template, values=values, **options)
        if not isinstance(template, str):
            return result
        result_str = str(result)
        lang_code = "en_US"
        request = values.get("request")
        if request:
            # For views
            lang_code = request.env.lang
        else:
            # For reports
            lang_match = re.search(r'data-oe-lang="([^"]+)"', result_str)
            if lang_match:
                lang_code = lang_match.group(1)
        view = self.env["ir.ui.view"]._get(template)
        mappings = (
            self.env["template.content.mapping"]
            .sudo()
            .search(
                [
                    ("template_id", "=", view.id),
                    "|",
                    ("lang", "=", lang_code),
                    ("lang", "=", False),
                ]
            )
        )
        if not mappings:
            return result
        global_mappings = [m for m in mappings if not m.domain]
        domain_mappings = [m for m in mappings if m.domain]
        result_str = self._apply_global_mappings(result_str, global_mappings)
        if not domain_mappings:
            return Markup(result_str)
        try:
            root = html.fromstring(result_str)
        except Exception:
            _logger.warning(
                "Failed to parse HTML for template %s, "
                "skipping domain-based mappings.",
                template,
            )
            return Markup(result_str)
        articles = root.xpath(
            '//div[contains(@class, "article")' " and @data-oe-model and @data-oe-id]"
        )
        if not articles:
            return Markup(result_str)
        if len(articles) == 1:
            # Single record → domain mappings can be applied globally
            article = articles[0]
            model_name = article.get("data-oe-model")
            res_id = int(article.get("data-oe-id"))
            result_str = self._apply_domain_mappings_single_record(
                result_str,
                model_name,
                res_id,
                domain_mappings,
            )
            return Markup(result_str)
        self._apply_domain_mappings_on_articles(root, domain_mappings)
        final_html = html.tostring(root, encoding="unicode")
        return Markup(final_html)
