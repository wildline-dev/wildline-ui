import gzip

from django.template import Context, Template, TemplateSyntaxError
from django.test import SimpleTestCase

# Keep the shared stylesheet small: it is inlined into every page. Pages are sent
# gzipped, so that's the size that matters on a weak signal; the raw budget catches
# anything that compresses badly.
CSS_BUDGET_BYTES = 40 * 1024
CSS_GZIP_BUDGET_BYTES = 8 * 1024


def render(source):
    return Template("{% load wildline_ui %}" + source).render(Context())


class WildlineCssTests(SimpleTestCase):
    def test_renders_inline_style_element(self):
        html = render("{% wildline_css %}")
        self.assertTrue(html.startswith("<style>"))
        self.assertTrue(html.endswith("</style>"))
        self.assertIn(".container", html)
        self.assertIn(".btn", html)

    def test_within_size_budget(self):
        css = render("{% wildline_css %}").encode()
        self.assertLess(len(css), CSS_BUDGET_BYTES)
        self.assertLess(len(gzip.compress(css, compresslevel=6)), CSS_GZIP_BUDGET_BYTES)

    def test_has_form_styles(self):
        html = render("{% wildline_css %}")
        for selector in (
            ".form-label",
            ".form-control",
            ".form-select",
            ".form-check-input",
        ):
            self.assertIn(selector, html)
        self.assertIn(".invalid-feedback", html)


class InlineStaticTests(SimpleTestCase):
    def test_inlines_file_unescaped(self):
        css = render('{% inline_static "wildline_ui/css/wildline-slim.css" %}')
        self.assertIn(">", css)
        self.assertNotIn("&gt;", css)

    def test_missing_file_raises(self):
        with self.assertRaises(TemplateSyntaxError):
            render('{% inline_static "nope.css" %}')
