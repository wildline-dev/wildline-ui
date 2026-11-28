"""Upload fields shared by every Wildline app (#8, #9): Share my location, and photos,
videos and recordings. Each gives a form a clean value; saving it is the app's job.

``LocationUploaderField`` asks the device where it is and gives a ``Location`` (or None).
``MediaUploaderField`` takes several files from one picker, checks each one's type from its
contents (never its name) and its size by kind, and gives a list of files with
``content_type`` and ``kind`` set.
"""

import json

import filetype
from django import forms
from django.template.defaultfilters import filesizeformat

from .location import KEYS, Location
from .media import AUDIO, PHOTO, VIDEO

MB = 1024 * 1024

# Accepted file types, by what the contents say they are. The same list dispatch's report
# attachments and the public site's forms used.
ACCEPTED = {
    "image/jpeg": PHOTO,
    "image/png": PHOTO,
    "image/webp": PHOTO,
    "image/heic": PHOTO,
    "image/heif": PHOTO,
    "video/mp4": VIDEO,
    "video/quicktime": VIDEO,
    "video/webm": VIDEO,
    "audio/mpeg": AUDIO,
    "audio/mp4": AUDIO,
    "audio/x-wav": AUDIO,
    "audio/ogg": AUDIO,
}
# For the file picker's accept attribute, by kind. HEIC and M4A need their extensions too.
ACCEPT_ATTRIBUTE = {
    PHOTO: "image/*,.heic,.heif",
    AUDIO: "audio/*,.m4a",
    VIDEO: "video/*",
}
# Each app sets its own limits (they depend on where files are kept); these are the defaults.
LIMITS = {PHOTO: 25 * MB, AUDIO: 25 * MB, VIDEO: 200 * MB}
KIND_WORDS = {PHOTO: "photo", VIDEO: "video", AUDIO: "recording"}

UPLOADER_MEDIA = forms.Media(
    css={"all": ["wildline_ui/css/uploads.css"]},
    js=["wildline_ui/js/uploads.js"],
)


def classify(upload, kinds=(PHOTO, VIDEO, AUDIO), limits=None):
    """Check an upload's type from its contents and its size; set content_type and kind on it.
    Raises ValidationError with a sentence for the person who sent it."""
    limits = {**LIMITS, **(limits or {})}
    upload.seek(0)
    guessed = filetype.guess(upload.read(8192))
    upload.seek(0)
    content_type = guessed.mime if guessed else ""
    kind = ACCEPTED.get(content_type)
    if kind not in kinds:
        wanted = " or ".join(KIND_WORDS[k] for k in kinds)
        raise forms.ValidationError(f"{upload.name} isn't a {wanted} this accepts.")
    if upload.size > limits[kind]:
        raise forms.ValidationError(
            f"{upload.name} is too large: {KIND_WORDS[kind]}s can be up to "
            f"{filesizeformat(limits[kind])}."
        )
    upload.content_type = content_type
    upload.kind = kind
    return upload


class LocationUploaderWidget(forms.MultiWidget):
    """Hidden latitude, longitude and accuracy inputs, and a "Share my location" button that
    fills them in where the browser allows it (static/wildline_ui/js/uploads.js)."""

    template_name = "wildline_ui/widgets/location_uploader.html"
    invalid = False  # set by a form to mark the button's box as needing attention

    def __init__(self, attrs=None, *, button_label="Share my location"):
        self.button_label = button_label
        super().__init__(
            {key: forms.HiddenInput(attrs={"data-wl-input": key}) for key in KEYS},
            attrs,
        )

    @property
    def is_hidden(self):
        return False  # its inputs are hidden, but the button shows

    @property
    def media(self):
        return UPLOADER_MEDIA

    def id_for_label(self, id_):
        return f"{id_}_button" if id_ else id_  # the label is for the button

    def decompress(self, value):
        location = Location.from_tuple(value) or Location.from_data(value)
        if not location:
            return [None, None, None]
        return [location.latitude, location.longitude, location.accuracy_m]

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        if not isinstance(value, list | tuple):
            value = self.decompress(value)
        context["widget"].update(
            location=Location.from_tuple(list(value)),
            invalid=self.invalid,
            button_label=self.button_label,
        )
        return context


class LocationUploaderField(forms.MultiValueField):
    """Where the device is, as a Location, or None if it wasn't shared. ``required`` means it
    must be shared."""

    widget = LocationUploaderWidget

    def __init__(self, *, required=False, **kwargs):
        fields = (
            forms.FloatField(min_value=-90, max_value=90, required=False),
            forms.FloatField(min_value=-180, max_value=180, required=False),
            forms.FloatField(min_value=0, required=False),
        )
        super().__init__(fields, required=False, require_all_fields=False, **kwargs)
        self.location_required = required

    def compress(self, data_list):
        latitude, longitude, accuracy = (list(data_list) + [None] * 3)[:3]
        if latitude is None or longitude is None:
            return None
        return Location(latitude, longitude, accuracy)

    def clean(self, value):
        location = super().clean(value)
        if self.location_required and not location:
            raise forms.ValidationError("Tap Share my location first.", code="required")
        return location


class MediaUploaderWidget(forms.ClearableFileInput):
    """A multiple file picker. With JavaScript, each chosen file shows under it with a preview
    (photos, made on the device), its size, a Remove button, and a warning straight away if
    it's too large or not a kind this takes."""

    template_name = "wildline_ui/widgets/media_uploader.html"
    allow_multiple_selected = True

    def __init__(
        self, attrs=None, *, kinds=(PHOTO, VIDEO, AUDIO), limits=None, max_files=10
    ):
        self.kinds = list(kinds)
        self.limits = {**LIMITS, **(limits or {})}
        self.max_files = max_files
        attrs = {
            "accept": ",".join(ACCEPT_ATTRIBUTE[kind] for kind in self.kinds),
            **(attrs or {}),
        }
        super().__init__(attrs)

    @property
    def media(self):
        return UPLOADER_MEDIA

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["widget"].update(
            kinds_json=json.dumps(self.kinds),
            limits_json=json.dumps({kind: self.limits[kind] for kind in self.kinds}),
            max_files=self.max_files,
        )
        return context


class MediaUploaderField(forms.FileField):
    """Several photos, videos or recordings from one picker, each checked by ``classify``."""

    widget = MediaUploaderWidget

    def __init__(
        self, *, kinds=(PHOTO, VIDEO, AUDIO), limits=None, max_files=10, **kwargs
    ):
        self.kinds = list(kinds)
        self.limits = {**LIMITS, **(limits or {})}
        self.max_files = max_files
        kwargs.setdefault(
            "widget",
            MediaUploaderWidget(kinds=kinds, limits=limits, max_files=max_files),
        )
        super().__init__(**kwargs)

    def clean(self, data, initial=None):
        files = [f for f in (data if isinstance(data, list | tuple) else [data]) if f]
        if not files:
            if self.required:
                raise forms.ValidationError(
                    self.error_messages["required"], code="required"
                )
            return []
        if len(files) > self.max_files:
            raise forms.ValidationError(f"Send up to {self.max_files} files at a time.")
        return [
            classify(
                super(MediaUploaderField, self).clean(f, initial),
                self.kinds,
                self.limits,
            )
            for f in files
        ]
