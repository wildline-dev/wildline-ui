"""A point on the map, shared by every Wildline app (#3).

``Location`` is the value a location picker or a "share my location" button gives a form, and
the JSON every app stores and sends: ``{"latitude", "longitude", "accuracy_m"}`` (accuracy is
left out when it isn't known, such as for a pin placed by hand).
"""

import json
from dataclasses import asdict, dataclass

KEYS = ("latitude", "longitude", "accuracy_m")


def _number(value):
    """A JSON number (or numeric text), or None."""
    if isinstance(value, bool) or value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


@dataclass(frozen=True)
class Location:
    latitude: float
    longitude: float
    accuracy_m: float | None = None

    @classmethod
    def from_data(cls, data):
        """From stored or sent data: a dict or its JSON. None without a usable point."""
        if isinstance(data, cls):
            return data
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except ValueError:
                return None
        if not isinstance(data, dict):
            return None
        latitude, longitude = (
            _number(data.get("latitude")),
            _number(data.get("longitude")),
        )
        if latitude is None or longitude is None:
            return None
        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            return None
        accuracy = _number(data.get("accuracy_m"))
        return cls(
            latitude, longitude, accuracy if accuracy is None or accuracy >= 0 else None
        )

    @classmethod
    def from_tuple(cls, values):
        """From a location tuple, (latitude, longitude[, accuracy_m]), or a form's inputs."""
        if isinstance(values, cls) or not isinstance(values, list | tuple):
            return cls.from_data(values)
        return cls.from_data(dict(zip(KEYS, values, strict=False)))

    def to_dict(self):
        return {key: value for key, value in asdict(self).items() if value is not None}

    def to_json(self):
        return json.dumps(self.to_dict())

    def __str__(self):
        point = f"{self.latitude:.5f}, {self.longitude:.5f}"
        if self.accuracy_m is not None:
            point += f" (±{self.accuracy_m:.0f} m)"
        return point


# What a point is, which sets its dot's colour and its line in the map's legend (#14).
PHOTO, SHARED, OTHER = "photo", "shared", "other"
KINDS = (PHOTO, SHARED, OTHER)
# The legend's words, by kind, and for the pin ("location"). Apps can pass their own.
LEGEND = {
    PHOTO: "Photo location",
    SHARED: "Shared location",
    OTHER: "Other location",
    "location": "Location",
}


@dataclass(frozen=True)
class Point:
    """A location to show on a map, with a label, such as where a photo was taken, and a kind
    (photo, shared or other) that sets its colour. In a picker, choosing a point sets the
    value to its location."""

    location: Location
    label: str = ""
    kind: str = OTHER

    @classmethod
    def coerce(cls, value):
        """A Point from a Point, a Location, a dict (location keys, label and kind), a
        (location, label[, kind]) tuple, or a location tuple (latitude, longitude[, accuracy_m
        [, label[, kind]]]). None if it has no usable location."""
        if isinstance(value, cls):
            return value
        if isinstance(value, Location):
            return cls(value)
        if isinstance(value, dict):
            location = Location.from_data(value)
            if not location:
                return None
            return cls(location, value.get("label") or "", _kind(value.get("kind")))
        if isinstance(value, list | tuple) and value:
            if not isinstance(value[0], int | float | str):
                location = Location.from_tuple(value[0])
                rest = list(value[1:])
            else:
                location = Location.from_tuple(value[:3])
                rest = list(value[3:])
            if not location:
                return None
            label = str(rest[0] or "") if rest else ""
            return cls(location, label, _kind(rest[1] if len(rest) > 1 else None))
        return None

    def to_dict(self):
        return {**self.location.to_dict(), "label": self.label, "kind": self.kind}


def _kind(value):
    return value if value in KINDS else OTHER


def points(values):
    """The usable points among values (see Point.coerce), as dicts for the map's JSON."""
    return [point.to_dict() for point in map(Point.coerce, values or ()) if point]


def legend(values, has_pin, words=None):
    """The map's legend (#14): (kind, words) for each kind of point on it, then the pin's, or
    [] for a map without points. ``words`` overrides LEGEND's, such as "Report location"."""
    words = {**LEGEND, **(words or {})}
    found = {point.kind for point in map(Point.coerce, values or ()) if point}
    if not found:
        return []
    rows = [(kind, words[kind]) for kind in KINDS if kind in found]
    return rows + ([("location", words["location"])] if has_pin else [])
