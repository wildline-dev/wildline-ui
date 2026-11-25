from functools import lru_cache

from django import template
from django.conf import settings
from django.contrib.staticfiles import finders
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()

WILDLINE_CSS = "wildline_ui/css/wildline-slim.css"


@lru_cache(maxsize=None)
def _read(path):
    found = finders.find(path)
    if not found:
        raise template.TemplateSyntaxError(f"inline_static: {path!r} not found")
    with open(found, encoding="utf-8") as fh:
        return fh.read()


@register.simple_tag
def inline_static(path):
    """Return a static file's contents for inlining, e.g. CSS in a <style> tag.

    Inlining saves a round trip, which is the slow part on a weak signal.
    Only use it with files from the codebase, never user-supplied content.
    """
    if settings.DEBUG:
        _read.cache_clear()
    return mark_safe(_read(path))


@register.simple_tag
def wildline_css():
    """Return the shared Wildline stylesheet as an inline <style> element."""
    return format_html("<style>{}</style>", inline_static(WILDLINE_CSS))
