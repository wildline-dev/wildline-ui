import json
from functools import cache

from django import template
from django.conf import settings
from django.contrib.staticfiles import finders
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .. import cards
from ..cards import OBJECT_CARD_MEDIA
from ..location import Location
from ..location import legend as location_legend
from ..location import points as location_points
from ..maps import MAP_MEDIA, map_options
from ..media import AUDIO_MEDIA, VIEWER_MEDIA

register = template.Library()

WILDLINE_CSS = "wildline_ui/css/wildline-slim.css"


@cache
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
def location_map(
    location=None, points=(), picker=False, label="Map", css_class="", legend=None
):
    """A map of a location (a red pin, with its accuracy as a circle) and points (location
    tuples, as dots coloured by kind), with a legend when it has points (#14). ``legend``
    renames the legend's entries, such as {"location": "Report location"}. Needs the map's
    scripts on the page: a form's media, or {% location_map_assets %}.
    """
    location = Location.from_tuple(location) if location else None
    return {
        "picker": picker,
        "label": label,
        "class": css_class,
        "options_json": json.dumps(map_options()),
        "value_json": json.dumps(location.to_dict() if location else None),
        "points_json": json.dumps(location_points(points)),
        "legend": location_legend(
            points, has_pin=picker or bool(location), words=legend
        ),
    }


@register.simple_tag
def location_map_assets():
    """Leaflet and the picker script, for pages that swap maps in later (such as with htmx)."""
    return MAP_MEDIA.render()


@register.filter
def object_card_parts(rows):
    """An Object card's rows, split into shown, folded and editing (wildline_ui.cards.parts)."""
    return cards.parts(rows)


@register.filter
def object_card_input(bound_field):
    """A form field's input alone, small, for editing a value in its row of an Object card."""
    return cards.inline_input(bound_field)


@register.simple_tag
def object_card_assets():
    """The Object card's stylesheet."""
    return OBJECT_CARD_MEDIA.render()


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
