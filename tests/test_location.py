import json

from django import forms
from django.template import Context, Template
from django.test import SimpleTestCase, override_settings

from wildline_ui.forms import LocationPickerField
from wildline_ui.location import Location, Point, points


class LocationTests(SimpleTestCase):
    def test_from_tuple_dict_and_json(self):
        expected = Location(36.6, -121.9, 12.0)
        self.assertEqual(Location.from_tuple((36.6, -121.9, 12)), expected)
        self.assertEqual(
            Location.from_data(
                {"latitude": "36.6", "longitude": -121.9, "accuracy_m": 12}
            ),
            expected,
        )
        self.assertEqual(Location.from_data(expected.to_json()), expected)
        self.assertEqual(Location.from_tuple((36.6, -121.9)), Location(36.6, -121.9))
        self.assertIsNone(Location.from_data([36.6, -121.9]))  # stored data is a dict

    def test_unusable_is_none(self):
        for data in (
            None,
            "",
            "nope",
            (91, 0),
            (0, 181),
            ("", ""),
            {"latitude": True, "longitude": 1},
        ):
            self.assertIsNone(Location.from_tuple(data), data)

    def test_negative_accuracy_dropped(self):
        self.assertIsNone(Location.from_tuple((1, 2, -5)).accuracy_m)

    def test_json_leaves_out_unknown_accuracy(self):
        self.assertEqual(
            json.loads(Location(1, 2).to_json()), {"latitude": 1, "longitude": 2}
        )

    def test_str(self):
        self.assertEqual(
            str(Location(36.6, -121.9, 12)), "36.60000, -121.90000 (±12 m)"
        )


class PointTests(SimpleTestCase):
    def test_coerce(self):
        here = Location(1, 2, 3)
        self.assertEqual(Point.coerce((1, 2, 3)), Point(here))
        self.assertEqual(Point.coerce((1, 2, 3, "Photo")), Point(here, "Photo"))
        self.assertEqual(Point.coerce((here, "Photo")), Point(here, "Photo"))
        self.assertEqual(
            Point.coerce(
                {"latitude": 1, "longitude": 2, "accuracy_m": 3, "label": "Caller"}
            ),
            Point(here, "Caller"),
        )
        self.assertEqual(Point.coerce(here), Point(here))
        self.assertIsNone(Point.coerce((None, None)))

    def test_points_skips_unusable(self):
        self.assertEqual(
            points([(1, 2), None, (99, 0), (Location(3, 4, 5), "Caller")]),
            [
                {"latitude": 1, "longitude": 2, "label": ""},
                {"latitude": 3, "longitude": 4, "accuracy_m": 5, "label": "Caller"},
            ],
        )


class PickerForm(forms.Form):
    location = LocationPickerField(points=[(1, 2, 30, "Photo")], locate=True)


class LocationPickerFieldTests(SimpleTestCase):
    def test_clean(self):
        form = PickerForm(
            {
                "location_latitude": "36.6",
                "location_longitude": "-121.9",
                "location_accuracy_m": "12",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["location"], Location(36.6, -121.9, 12))

    def test_empty_is_none(self):
        form = PickerForm(
            {
                "location_latitude": "",
                "location_longitude": "",
                "location_accuracy_m": "",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertIsNone(form.cleaned_data["location"])

    def test_half_a_point_is_an_error(self):
        form = PickerForm({"location_latitude": "36.6", "location_longitude": ""})
        self.assertFalse(form.is_valid())
        self.assertIn("incomplete", form.errors["location"][0])

    def test_out_of_range(self):
        self.assertFalse(
            PickerForm(
                {"location_latitude": "95", "location_longitude": "0"}
            ).is_valid()
        )

    def test_required(self):
        class Required(forms.Form):
            location = LocationPickerField(required=True)

        form = Required({})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["location"], ["Place the pin on the map."])

    def test_has_changed(self):
        initial = {"location": Location(36.6, -121.9)}
        same = PickerForm(
            {"location_latitude": "36.600000", "location_longitude": "-121.900000"},
            initial=initial,
        )
        moved = PickerForm(
            {"location_latitude": "36.7", "location_longitude": "-121.9"},
            initial=initial,
        )
        self.assertEqual(same.changed_data, [])
        self.assertEqual(moved.changed_data, ["location"])

    def test_renders_inputs_map_and_points(self):
        form = PickerForm(initial={"location": Location(36.6, -121.9, 12)})
        html = str(form["location"])
        self.assertIn('data-wl-input="latitude"', html)
        self.assertIn('value="36.6"', html)
        self.assertIn("data-wl-map-picker", html)
        self.assertNotIn("data-wl-map ", html)  # the picker's map is the only one
        self.assertIn("data-wl-location-locate", html)
        self.assertIn("&quot;label&quot;: &quot;Photo&quot;", html)
        self.assertIn("&quot;accuracy_m&quot;: 12.0", html)

    def test_accuracy_slider(self):
        html = str(PickerForm()["location"])
        self.assertIn("data-wl-accuracy-slider", html)
        self.assertIn('max="10"', html)
        self.assertIn("[10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000]", html)

    def test_points_can_be_set_per_form(self):
        form = PickerForm()
        form.fields["location"].points = [(5, 6, None, "Caller")]
        html = str(form["location"])
        self.assertIn("Caller", html)
        self.assertNotIn("Photo", html)

    def test_media_is_leaflet_and_picker(self):
        media = str(PickerForm().media)
        self.assertIn("wildline_ui/vendor/leaflet/leaflet.js", media)
        self.assertIn("wildline_ui/js/location-picker.js", media)
        self.assertIn("wildline_ui/css/location-picker.css", media)


def render(source, **context):
    return Template("{% load wildline_ui %}" + source).render(Context(context))


class LocationCardTests(SimpleTestCase):
    def test_card_with_location(self):
        html = render(
            '{% include "wildline_ui/cards/location.html" %}',
            location=Location(1, 2, 3),
        )
        self.assertIn('class="card wl-location-card"', html)
        self.assertIn("Location</h3>", html)
        self.assertIn("data-wl-map ", html)
        self.assertIn("1.00000, 2.00000 (±3 m)", html)

    def test_card_without_location(self):
        html = render(
            '{% include "wildline_ui/cards/location.html" with empty_text="Not known." %}',
            location=None,
        )
        self.assertNotIn("data-wl-map", html)
        self.assertIn("Not known.", html)

    def test_card_with_only_points(self):
        html = render(
            '{% include "wildline_ui/cards/location.html" %}',
            location=None,
            points=[(1, 2, 5, "Photo seal.jpg"), (3, 4)],
        )
        self.assertIn("data-wl-map ", html)
        self.assertIn(
            "No pin yet. The dots on the map are possible locations: Photo seal.jpg; 3.00000, 4.00000.",
            html,
        )

    def test_card_with_picker(self):
        form = PickerForm()
        html = render(
            '{% include "wildline_ui/cards/location.html" with field=form.location %}',
            form=form,
            location=None,
        )
        self.assertIn("data-wl-map-picker", html)

    def test_card_blocks_extend(self):
        html = Template(
            '{% extends "wildline_ui/cards/location.html" %}'
            "{% block actions %}<button>Edit</button>{% endblock %}"
            "{% block editor %}<form>picker</form>{% endblock %}"
        ).render(Context({"location": None}))
        self.assertIn("<button>Edit</button>", html)
        self.assertIn("<form>picker</form>", html)

    @override_settings(
        WILDLINE_UI_MAP={"tile_url": "https://tiles.example/{z}/{x}/{y}.png"}
    )
    def test_map_options_from_settings(self):
        html = render("{% location_map location %}", location=(1, 2))
        self.assertIn("tiles.example", html)
        self.assertIn("&quot;pin_zoom&quot;: 15", html)

    def test_map_assets(self):
        html = render("{% location_map_assets %}")
        self.assertIn("leaflet.css", html)
        self.assertIn("location-picker.js", html)
