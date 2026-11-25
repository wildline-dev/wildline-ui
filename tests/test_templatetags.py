from django.template import Context, Template, TemplateSyntaxError
from django.test import SimpleTestCase

# Keep the shared stylesheet small: it is inlined into every page.
CSS_BUDGET_BYTES = 32 * 1024


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
        self.assertLess(len(render("{% wildline_css %}").encode()), CSS_BUDGET_BYTES)


class InlineStaticTests(SimpleTestCase):
    def test_inlines_file_unescaped(self):
        css = render('{% inline_static "wildline_ui/css/wildline-slim.css" %}')
        self.assertIn(">", css)
        self.assertNotIn("&gt;", css)

    def test_missing_file_raises(self):
        with self.assertRaises(TemplateSyntaxError):
            render('{% inline_static "nope.css" %}')
