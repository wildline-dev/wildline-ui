import json
from functools import lru_cache

from django import template
from django.conf import settings
from django.contrib.staticfiles import finders
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from ..location import Location, Point
from ..location import points as location_points
from ..maps import MAP_MEDIA, map_options
from ..media import AUDIO_MEDIA, VIEWER_MEDIA

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
    location = Location.from_tuple(location) if location else None
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


@register.filter
def point_labels(values):
    """Each usable point's label, or its location if it has none."""
    found = [Point.coerce(value) for value in values or ()]
    return [point.label or str(point.location) for point in found if point]


@register.inclusion_tag("wildline_ui/audio_player.html")
def audio_player(src, duration=None, label="", error=""):
    """A voicemail's or recording's player (#7). Needs {% audio_player_assets %} on the page."""
    return {"src": src, "duration": duration, "label": label, "error": error}


@register.simple_tag
def audio_player_assets():
    """wavesurfer.js and the player script, for pages with audio players (#7)."""
    return AUDIO_MEDIA.render()


@register.simple_tag
def media_viewer_assets():
    """The Media card's viewer and its audio players (#6, #7)."""
    return VIEWER_MEDIA.render()
