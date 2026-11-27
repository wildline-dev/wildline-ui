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


# A related record (a foreign key), picked by searching (#5).

RECORD_SEARCH_MEDIA = forms.Media(
    css={"all": ["wildline_ui/css/cards.css", "wildline_ui/css/object-card.css"]},
    js=["wildline_ui/js/record-search.js"],
)


class RecordSearchWidget(forms.Widget):
    """A hidden input with the record's ID, and a search box that sets it.

    As you type, ``wildline_ui/js/record-search.js`` asks ``search_url`` for ``?q=<text>`` and
    lists what it answers: JSON ``{"results": [{"id", "label", "detail"}]}``. Choosing one sets
    the ID. Without JavaScript the record stays as it was.
    """

    template_name = "wildline_ui/widgets/record_search.html"

    def __init__(self, attrs=None, *, search_url="", placeholder="Search"):
        self.search_url = search_url
        self.placeholder = placeholder
        self.current_label = None  # set by RecordSearchField
        super().__init__(attrs)

    @property
    def media(self):
        return RECORD_SEARCH_MEDIA

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        label = self.current_label(value) if self.current_label and value else ""
        context["widget"].update(
            search_url=self.search_url, placeholder=self.placeholder, current=label
        )
        return context


class RecordSearchField(forms.ModelChoiceField):
    """A foreign key picked by searching, rather than from a list of every record.

    ``search_url`` answers the widget's searches (see ``RecordSearchWidget``) from the same
    records as ``queryset``, which checks the choice. ``label_from_instance`` names the record
    in the search box.
    """

    widget = RecordSearchWidget

    def __init__(self, queryset, *, search_url, placeholder="Search", **kwargs):
        kwargs.setdefault(
            "widget", RecordSearchWidget(search_url=search_url, placeholder=placeholder)
        )
        super().__init__(queryset, **kwargs)
        self.widget.current_label = self._label_for

    def _label_for(self, value):
        if isinstance(value, self.queryset.model):
            return self.label_from_instance(value)
        try:
            found = self.queryset.filter(pk=value).first()
        except (ValueError, TypeError):
            return ""
        return self.label_from_instance(found) if found else ""

    def __deepcopy__(self, memo):
        result = super().__deepcopy__(memo)
        result.widget.current_label = result._label_for
        return result
