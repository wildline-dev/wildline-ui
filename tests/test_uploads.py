import base64

from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template import Context, Template
from django.test import SimpleTestCase
from django.utils.datastructures import MultiValueDict

from wildline_ui.location import Location
from wildline_ui.media import AUDIO, PHOTO, VIDEO
from wildline_ui.uploads import (
    MB,
    UPLOADER_MEDIA,
    LocationUploaderField,
    MediaUploaderField,
    classify,
)

PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
)
MP4 = b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom" + b"\x00" * 64


def png(name="seal.png"):
    return SimpleUploadedFile(name, PNG, content_type="image/png")


def mp4(name="beach.mp4", size=None):
    body = MP4 + b"\x00" * max(0, (size or 0) - len(MP4))
    return SimpleUploadedFile(name, body, content_type="video/mp4")


class ShareForm(forms.Form):
    location = LocationUploaderField()


class RequiredShareForm(forms.Form):
    location = LocationUploaderField(required=True)


class FilesForm(forms.Form):
    files = MediaUploaderField(
        kinds=(PHOTO, VIDEO), limits={VIDEO: 1 * MB}, max_files=2, required=False
    )


class LocationUploaderTests(SimpleTestCase):
    def test_shared_location(self):
        form = ShareForm(
            {
                "location_latitude": "36.6",
                "location_longitude": "-121.9",
                "location_accuracy_m": "12",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["location"], Location(36.6, -121.9, 12))

    def test_not_shared(self):
        form = ShareForm({})
        self.assertTrue(form.is_valid())
        self.assertIsNone(form.cleaned_data["location"])

    def test_required(self):
        form = RequiredShareForm({})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["location"], ["Tap Share my location first."])

    def test_out_of_range(self):
        form = ShareForm({"location_latitude": "136", "location_longitude": "1"})
        self.assertFalse(form.is_valid())

    def test_renders_button_and_hidden_inputs(self):
        html = str(ShareForm(auto_id="id_%s")["location"])
        self.assertIn('id="id_location_button"', html)
        self.assertIn("data-wl-share-location hidden", html)
        self.assertIn('type="hidden" name="location_latitude"', html)
        self.assertIn('data-wl-input="accuracy_m"', html)
        self.assertIn("needs a browser that allows it", html)

    def test_label_points_at_button(self):
        self.assertIn('for="id_location_button"', ShareForm()["location"].label_tag())

    def test_shows_a_shared_location_again(self):
        form = ShareForm(
            initial={"location": {"latitude": 1, "longitude": 2, "accuracy_m": 30}}
        )
        html = str(form["location"])
        self.assertIn('name="location_latitude" value="1.0"', html)
        self.assertIn("Location shared (within about 30 m).", html)

    def test_invalid_flag(self):
        form = ShareForm()
        form.fields["location"].widget.invalid = True
        self.assertIn("is-invalid", str(form["location"]))

    def test_media(self):
        self.assertEqual(str(ShareForm().media), str(UPLOADER_MEDIA))


class MediaUploaderTests(SimpleTestCase):
    def form(self, *files):
        return FilesForm({}, MultiValueDict({"files": list(files)}))

    def test_classifies_each_file(self):
        form = self.form(png(), mp4())
        self.assertTrue(form.is_valid(), form.errors)
        files = form.cleaned_data["files"]
        self.assertEqual(
            [(f.kind, f.content_type) for f in files],
            [(PHOTO, "image/png"), (VIDEO, "video/mp4")],
        )

    def test_nothing_chosen(self):
        form = self.form()
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["files"], [])

    def test_type_from_contents_not_name(self):
        fake = SimpleUploadedFile(
            "seal.png", b"not an image at all", content_type="image/png"
        )
        form = self.form(fake)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["files"], ["seal.png isn't a photo or video this accepts."]
        )

    def test_kind_not_taken(self):
        mp3 = SimpleUploadedFile("call.mp3", b"ID3\x03\x00\x00\x00" + b"\x00" * 64)
        self.assertIn("isn't a photo or video", self.form(mp3).errors["files"][0])

    def test_too_large(self):
        form = self.form(mp4(size=2 * MB))
        self.assertEqual(
            form.errors["files"],
            ["beach.mp4 is too large: videos can be up to 1.0\xa0MB."],
        )

    def test_too_many(self):
        form = self.form(png("a.png"), png("b.png"), png("c.png"))
        self.assertEqual(form.errors["files"], ["Send up to 2 files at a time."])

    def test_renders_picker(self):
        html = str(FilesForm()["files"])
        self.assertIn('type="file" name="files"', html)
        self.assertIn("multiple", html)
        self.assertIn('accept="image/*,.heic,.heif,video/*"', html)
        self.assertIn('data-kinds="[&quot;photo&quot;, &quot;video&quot;]"', html)
        self.assertIn(f"&quot;video&quot;: {MB}", html)
        self.assertIn('data-max-files="2"', html)

    def test_classify_defaults(self):
        self.assertEqual(classify(png()).kind, PHOTO)
        with self.assertRaises(forms.ValidationError):
            classify(png(), kinds=(AUDIO,))


class InlineMediaTests(SimpleTestCase):
    def test_inlines_css_and_js(self):
        html = Template("{% load wildline_ui %}{% inline_media media %}").render(
            Context({"media": UPLOADER_MEDIA})
        )
        self.assertIn("<style>", html)
        self.assertIn(".wl-upload-list", html)
        self.assertIn("<script>", html)
        self.assertIn("data-wl-media-uploader", html)
        self.assertNotIn("src=", html)


class InvalidMarkTests(SimpleTestCase):
    def test_invalid_input_marks_the_box(self):
        # So Bootstrap's ".is-invalid ~ .invalid-feedback" shows an error after the widget.
        form = FilesForm()
        form.fields["files"].widget.attrs["class"] = "form-control is-invalid"
        self.assertIn('class="wl-media-uploader is-invalid"', str(form["files"]))
        self.assertIn('class="wl-media-uploader"', str(FilesForm()["files"]))
