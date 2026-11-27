# wildline-ui

Shared low-bandwidth styling for Wildline Django apps: a slim Bootstrap 5.3 build (about 7.2 KB gzipped, no JavaScript) and template tags that inline it, so each page loads in a single request. It also has shared cards, starting with a location picker (the only part with JavaScript, loaded only on pages with a map).

## Use it in an app

```sh
uv add "wildline-ui @ git+https://github.com/wildline-dev/wildline-ui@v0.1.0"
```

Add `"wildline_ui"` to `INSTALLED_APPS` (it needs `django.contrib.staticfiles`), then in your base template:

```django
{% load wildline_ui %}
<head>
  ...
  {% wildline_css %}
</head>
```

`{% inline_static "path/in/static.css" %}` inlines any other static file the same way. Use it only for files from the codebase.

## Location picker and Location card

For maps of a location and picking one. A location is a `wildline_ui.location.Location(latitude, longitude, accuracy_m)`; the JSON every app stores and sends is `{"latitude", "longitude", "accuracy_m"}`, with accuracy left out when it isn't known.

In a form, `LocationPickerField` gives you a `Location` (or `None`). Its map shows *points*, location tuples `(latitude, longitude, accuracy_m, label)` such as where a photo was taken or the caller's shared location. Clicking a point sets the pin to it, with its accuracy. Clicking the map places a pin by hand, with no accuracy:

```python
from wildline_ui.forms import LocationPickerField

class PlaceForm(forms.Form):
    location = LocationPickerField(points=[(36.6, -121.9, 12, "Caller's location")], locate=True)
```

`locate=True` adds a "Use my location" button. You can set points per form with `form.fields["location"].points = [...]`. The field's media brings Leaflet and `wildline_ui/js/location-picker.js`, so render `{{ form.media }}`. Pages that swap maps in later, such as with htmx, should load them up front with `{% location_map_assets %}`.

The Location card shows a read-only map, the location as text and, given `field`, the picker:

```django
{% include "wildline_ui/cards/location.html" with location=report.location points=points field=form.location %}
```

To add header buttons or wrap the picker in your own form, extend `wildline_ui/cards/location.html` and fill its `actions` and `editor` blocks. `{% location_map location points=points %}` is the read-only map on its own.

Tiles come from OpenStreetMap by default. Override the tile URL, attribution or starting view with `WILDLINE_UI_MAP = {"tile_url": ..., "center": [lat, lng], "zoom": 4}` in settings (see `wildline_ui/maps.py`).

## Change the styles

The compiled CSS in `src/wildline_ui/static/wildline_ui/css/` is committed, so apps don't need Node. To add a Bootstrap component or utility, edit `assets/scss/wildline-slim.scss`, then:

```sh
npm ci
npm run build:css
```

Bump `version` in `pyproject.toml`, tag the release (e.g. `v0.2.0`), and update the tag in each app.

## Tests

```sh
DJANGO_SETTINGS_MODULE=tests.settings uv run python -m django test --pythonpath=.
```
