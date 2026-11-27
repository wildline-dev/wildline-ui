"""Map settings shared by the location picker and read-only maps (#3).

Override any of these in a project's settings with ``WILDLINE_UI_MAP = {...}``.
"""

from django.conf import settings
from django.forms import Media

DEFAULTS = {
    "tile_url": "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
    "attribution": '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    " contributors",
    "max_zoom": 19,
    # OSM's tile servers refuse requests without a Referer (wildline-dispatch#59), and Django's
    # default Referrer-Policy (same-origin) drops it on cross-origin requests. Send our origin.
    "referrer_policy": "strict-origin-when-cross-origin",
    "center": [39.5, -98.35],  # the continental US, until there's a pin
    "zoom": 4,
    "pin_zoom": 15,
}


def map_options():
    return {**DEFAULTS, **getattr(settings, "WILDLINE_UI_MAP", {})}


# Leaflet and the picker script, only on pages with a map. Pages that swap maps in with htmx
# should load these up front with {% location_map_assets %}.
MAP_MEDIA = Media(
    css={
        "all": [
            "wildline_ui/css/cards.css",
            "wildline_ui/vendor/leaflet/leaflet.css",
            "wildline_ui/css/location-picker.css",
        ]
    },
    js=["wildline_ui/vendor/leaflet/leaflet.js", "wildline_ui/js/location-picker.js"],
)
