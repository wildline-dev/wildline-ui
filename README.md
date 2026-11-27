# wildline-ui

Shared low-bandwidth styling for Wildline Django apps: a slim Bootstrap 5.3 build (about 7.2 KB gzipped, no JavaScript) and template tags that inline it, so each page loads in a single request. It also has shared cards: a location picker (the only part with JavaScript, loaded only on pages with a map) and an Object card for any record's fields.

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

## Object card

Shows a record's fields and edits them in place, for any kind of record. The card only displays a dict; the view builds it, takes the POST, validates its own forms and renders the card again. Rows with a value show; hidden and empty ones fold under "Show all (N more)". With `edit`, a pencil turns each row's value into its inputs in the same row, saved with one Save. Hovering a label shows its help. It needs no JavaScript: the pencil is a checkbox and "Show all" a `<details>`.

```python
form = AnimalForm(instance=animal)
card = {
    "id": "animal-box",
    "title": "Animal",
    "edit": {"action": url, "hidden": {"version": animal.version}, "label": "Edit animal"},
    "rows": [
        {"label": "Species", "help": "What kind of animal", "text": animal.species, "inputs": [form["species"]]},
        {"label": "Band", "text": animal.band, "hidden": True},  # read-only while editing
    ],
}
```

```django
{% load wildline_ui %}
{% object_card_assets %}  {# in the page's head #}
{% include "wildline_ui/cards/object.html" with card=card %}
```

Each row takes `label`, `help`, `text` (empty shows "Not answered"), `hidden`, `wide` (no label, the full width), `template` and `value` (a custom display, such as a map, given `row` and `value`) and `inputs` (bound form fields). `edit` takes `action`, `hidden` (extra hidden inputs), `multipart`, `label` (the pencil's name), `open` (show the form, such as after errors), `errors` (messages above the inputs) and `text` (a text button, for apps without Bootstrap Icons). Rows can be dicts or objects; see `wildline_ui/cards.py`.

A row for a related record (a foreign key) takes `related`, `{"url": ..., "label": "Open contact"}`: its value shows in an inset box with a button to the record's page. To pick another one while editing, give the row a `RecordSearchField`:

```python
from wildline_ui.forms import RecordSearchField

reporting_party = RecordSearchField(ContactDetail.objects.all(), search_url=reverse("contacts:search"))
```

It's a `ModelChoiceField` whose widget is a search box: as you type, `wildline_ui/js/record-search.js` asks `search_url` for `?q=<text>`, which answers `{"results": [{"id", "label", "detail"}]}`. Render `{{ form.media }}` (or load the script up front on pages that swap the form in). To add header buttons or something under the rows, extend `wildline_ui/cards/object.html` and fill its `actions` and `footer` blocks. `{{ field|object_card_input }}` renders any field's input the same small way.

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
