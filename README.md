# wildline-ui

Shared low-bandwidth styling for Wildline Django apps: a slim Bootstrap 5.3 build (about 7.2 KB gzipped, no JavaScript) and template tags that inline it, so each page loads in a single request. It also has shared cards: a location picker (the only part with JavaScript, loaded only on pages with a map) an Object card for any record's fields, and a Backlinks card for the records that link to one.

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

`locate=True` adds a "Use my location" button. The pin is a red dot inside a red circle as large as its accuracy; the accuracy slider sets a rough one, anywhere from 10 m to 10 km. Drag the dot or click elsewhere to move it. A "Clear pin" button sits under the map; to put it with your form's own buttons instead, pass `clear=False` and add `<button type="button" data-wl-location-clear>Clear pin</button>` anywhere in the form. You can set points per form with `form.fields["location"].points = [...]`. The field's media brings Leaflet and `wildline_ui/js/location-picker.js`, so render `{{ form.media }}`. Pages that swap maps in later, such as with htmx, should load them up front with `{% location_map_assets %}`.

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

Each row takes `label`, `help`, `text` (empty shows "Not answered"), `hidden`, `wide` (no label, the full width), `template` and `value` (a custom display, such as a map, given `row` and `value`), `inputs` (bound form fields) and `edit_only` (a row only the form shows, such as "Add phone"). `edit` takes `action`, `hidden` (extra hidden inputs), `multipart`, `label` (the pencil's name), `open` (show the form, such as after errors), `errors` (messages above the inputs) and `text` (a text button, for apps without Bootstrap Icons). Rows can be dicts or objects; see `wildline_ui/cards.py`.

A row for a related record (a foreign key) takes `related`, `{"url": ..., "label": "Open contact"}`: its value shows in an inset box with an arrow to the record's page (`label` names the arrow for screen readers). To pick another one while editing, give the row a `RecordSearchField`:

```python
from wildline_ui.forms import RecordSearchField

reporting_party = RecordSearchField(ContactDetail.objects.all(), search_url=reverse("contacts:search"))
```

It's a `ModelChoiceField` whose widget is a search box: as you type, `wildline_ui/js/record-search.js` asks `search_url` for `?q=<text>`, which answers `{"results": [{"id", "label", "detail"}]}`. Render `{{ form.media }}` (or load the script up front on pages that swap the form in). To add header buttons or something under the rows, extend `wildline_ui/cards/object.html` and fill its `actions` and `footer` blocks. `{{ field|object_card_input }}` renders any field's input the same small way.

## Backlinks card

Lists the records that link to the one shown, such as the reports a contact made or a stranding's assessments. Like the Object card, it shows a dict the view builds. Each item is an inset box like a related record's, with an arrow to its page:

```python
card = {
    "id": "contact-reports",
    "title": "Reports",
    "empty_text": "No reports.",
    "items": [{"title": "26-00001", "badge": "Closed", "lines": ["Nov 27 11:40 PM"], "url": report_url, "label": "Open report 26-00001"}],
}
```

```django
{% include "wildline_ui/cards/backlinks.html" with card=card %}
```

An item's `fields`, `[{"label", "text"}]`, show as "Label: text" lines under its title. The view decides which, such as a record's summary fields or all of them. An item can take `template` and `value` for a custom display. It uses the Object card's stylesheet, `{% object_card_assets %}`.

## Media and Audio cards

For a record's photos, videos and recordings. The cards take a list of item dicts that the view builds (see `wildline_ui/media.py`):

```python
from wildline_ui.media import PHOTO, item, remove

items = [
    item(7, PHOTO, photo.url, "seal.jpg", thumbnail_url=..., preview_url=..., caption="seal.jpg · 9:10 PM",
         remove=remove(remove_url, version=report.version)),
]
```

```django
{% include "wildline_ui/cards/media.html" with items=items card_id="media" %}
{% include "wildline_ui/cards/audio.html" with items=voicemails title="Voicemail" %}
```

- **Media card**: photos and videos show as a grid of thumbnails. Each opens a full-screen viewer, a native `<dialog>`; the full-size photo loads only when it's opened, and a video stops when it closes. Without JavaScript, a thumbnail is a link to the original. Recordings show as players. Any element with `data-wl-media-open="#<card_id>-<key>"` opens an item's viewer. Extend it to fill the `actions` and `editor` blocks, such as an upload form.
- **Audio card** and `{% audio_player src duration label error %}`: play/pause, a waveform and the time, drawn by wavesurfer.js (vendored). Audio over 10 minutes gets a plain progress bar and downloads only when played. Playing one player pauses the others. Without JavaScript, the browser's own player shows.

Load the scripts with `{% media_viewer_assets %}` (the Media card) or `{% audio_player_assets %}` (players only). Neither needs Bootstrap's JavaScript; icons are inline SVG.

## Upload fields

For forms that take a location or files from the person filling them in (`wildline_ui/uploads.py`):

```python
from wildline_ui.media import PHOTO, VIDEO
from wildline_ui.uploads import MB, LocationUploaderField, MediaUploaderField

class ReportForm(forms.Form):
    location = LocationUploaderField(required=False)  # a Location, or None
    files = MediaUploaderField(kinds=(PHOTO, VIDEO), limits={VIDEO: 50 * MB}, max_files=10, required=False)
```

- **LocationUploaderField**: a "Share my location" button that asks the device where it is and fills in hidden latitude, longitude and accuracy inputs. The button shows only where the browser can share a location. `required=True` asks for it with "Tap Share my location first." Store `location.to_dict()` or its three numbers.
- **MediaUploaderField**: one picker for several files. Each chosen file shows with a preview, its size and a Remove button, and a warning straight away if it's too large or not a kind the field takes. The server checks each file's type from its contents (never its name) and its size by kind; `clean` returns a list of files with `content_type` and `kind` set. Saving them is the app's job.

Both bring `form.media` (a small script and stylesheet, no Bootstrap JavaScript). Pages that should load in one request can inline it with `{% inline_media form.media %}`.

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
