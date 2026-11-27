import json
from functools import lru_cache

from django import template
from django.conf import settings
from django.contrib.staticfiles import finders
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from ..location import Location
from ..location import points as location_points
from ..maps import MAP_MEDIA, map_options

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


@register.inclusion_tag("wildline_ui/map.html")
def location_map(location=None, points=(), picker=False, label="Map", css_class=""):
    """A map of a location (a pin, with its accuracy as a circle) and points (location tuples,
    as dots). Needs the map's scripts on the page: a form's media, or {% location_map_assets %}.
    """
    location = Location.from_data(location) if location else None
    return {
        "picker": picker,
        "label": label,
        "class": css_class,
        "options_json": json.dumps(map_options()),
        "value_json": json.dumps(location.to_dict() if location else None),
        "points_json": json.dumps(location_points(points)),
    }


@register.simple_tag
def location_map_assets():
    """Leaflet and the picker script, for pages that swap maps in later (such as with htmx)."""
    return MAP_MEDIA.render()
