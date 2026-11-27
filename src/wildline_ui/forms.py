"""The location picker as a form field (#3): a map to place a pin on, and any points (such as
where a photo was taken) to choose from. Its value is a ``Location``, or None."""

import json

from django import forms

from .location import KEYS, Location, points
from .maps import MAP_MEDIA, map_options


# The accuracy slider's steps, in metres (#3): from a pin on the spot to "somewhere in town".
ACCURACY_STEPS = (10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000)


class LocationPickerWidget(forms.MultiWidget):
    """Hidden latitude, longitude and accuracy inputs, and the map that sets them.

    ``points`` are location tuples to show and choose from (see ``location.Point``).
    ``locate`` adds a "Use my location" button that asks the device for its position.
    Its accuracy slider sets a rough accuracy, shown as a circle, for a pin placed by hand.
    """

    template_name = "wildline_ui/widgets/location_picker.html"

    def __init__(self, attrs=None, *, points=(), locate=False, help_text=None):
        self.points = points
        self.locate = locate
        self.help_text = help_text
        super().__init__(
            {key: forms.HiddenInput(attrs={"data-wl-input": key}) for key in KEYS},
            attrs,
        )

    @property
    def is_hidden(self):
        return False  # its inputs are hidden, but the map shows

    @property
    def media(self):
        return MAP_MEDIA

    def decompress(self, value):
        location = Location.from_tuple(value)
        if not location:
            return [None, None, None]
        return [location.latitude, location.longitude, location.accuracy_m]

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        if not isinstance(value, list | tuple):
            value = self.decompress(value)
        context["widget"].update(
            location=Location.from_tuple(list(value)),
            points=points(self.points),
            options=map_options(),
            locate=self.locate,
            help_text=self.help_text,
            accuracy_steps=ACCURACY_STEPS,
            accuracy_steps_json=json.dumps(ACCURACY_STEPS),
        )
        return context


class LocationPickerField(forms.MultiValueField):
    widget = LocationPickerWidget

    def __init__(self, *, points=(), locate=False, required=False, **kwargs):
        fields = (
            forms.FloatField(min_value=-90, max_value=90, required=False),
            forms.FloatField(min_value=-180, max_value=180, required=False),
            forms.FloatField(min_value=0, required=False),
        )
        kwargs.setdefault("widget", LocationPickerWidget(points=points, locate=locate))
        super().__init__(fields, required=required, require_all_fields=False, **kwargs)
        self.error_messages["required"] = "Place the pin on the map."
        self.error_messages["incomplete"] = (
            "Set the pin again: its position was incomplete."
        )

    @property
    def points(self):
        return self.widget.points

    @points.setter
    def points(self, value):
        self.widget.points = value

    def compress(self, data_list):
        latitude, longitude, accuracy = (list(data_list) + [None] * 3)[:3]
        if latitude is None and longitude is None:
            return None
        if latitude is None or longitude is None:
            raise forms.ValidationError(
                self.error_messages["incomplete"], code="incomplete"
            )
        return Location(latitude, longitude, accuracy)

    def has_changed(self, initial, data):
        if self.disabled:
            return False
        return Location.from_tuple(initial) != Location.from_tuple(data)
