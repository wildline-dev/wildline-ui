from django.template import Context, Template
from django.test import SimpleTestCase

from wildline_ui.media import AUDIO, PHOTO, VIDEO, item, remove


def render(source, **context):
    return Template("{% load wildline_ui %}" + source).render(Context(context))


PHOTO_ITEM = item(
    7,
    PHOTO,
    "/files/7",
    "seal.jpg",
    thumbnail_url="/files/7/thumb",
    preview_url="/files/7/preview",
    caption="seal.jpg · 9:10 PM",
    remove=remove("/reports/1/files/7/remove/", version=3),
)
VIDEO_ITEM = item(8, VIDEO, "/files/8", "beach.mp4")
AUDIO_ITEM = item(9, AUDIO, "/files/9", "call.m4a", duration=900, error="Gone.")


class ItemTests(SimpleTestCase):
    def test_defaults(self):
        self.assertEqual(
            item(1, AUDIO, "/a"),
            {
                "key": 1,
                "kind": "audio",
                "url": "/a",
                "name": "",
                "thumbnail_url": "",
                "preview_url": "",
                "caption": "",
                "duration": None,
                "error": "",
                "remove": None,
            },
        )


class AudioPlayerTests(SimpleTestCase):
    def test_player(self):
        html = render('{% audio_player "/v.mp3" 42 "Voicemail" "Gone." %}')
        self.assertIn('data-wl-audio data-src="/v.mp3" data-duration="42"', html)
        self.assertIn('aria-label="Play Voicemail"', html)
        self.assertIn(
            '<audio controls preload="none" src="/v.mp3"', html
        )  # without JavaScript
        self.assertIn("Gone.", html)
        self.assertIn('data-wl-audio-icon="pause"', html.replace("=pause", '="pause"'))

    def test_unknown_duration(self):
        self.assertIn('data-duration=""', render('{% audio_player "/v.mp3" %}'))

    def test_assets(self):
        html = render("{% audio_player_assets %}")
        self.assertIn("wavesurfer.min.js", html)
        self.assertIn("audio-player.js", html)
        self.assertNotIn("media-viewer.js", html)
        viewer = render("{% media_viewer_assets %}")
        self.assertIn("wavesurfer.min.js", viewer)
        self.assertIn("media-viewer.js", viewer)
        self.assertIn("cards.css", viewer)


class AudioCardTests(SimpleTestCase):
    def test_items(self):
        html = render(
            '{% include "wildline_ui/cards/audio.html" with title="Voicemail" %}',
            items=[AUDIO_ITEM],
        )
        self.assertIn("Voicemail</h3>", html)
        self.assertIn('data-src="/files/9" data-duration="900"', html)
        self.assertIn("call.m4a", html)

    def test_empty(self):
        html = render('{% include "wildline_ui/cards/audio.html" %}', items=[])
        self.assertIn("No recordings.", html)


class MediaCardTests(SimpleTestCase):
    def html(self, items, **context):
        return render(
            '{% include "wildline_ui/cards/media.html" %}', items=items, **context
        )

    def test_photo_opens_its_viewer(self):
        html = self.html([PHOTO_ITEM])
        self.assertIn('id="media"', html)
        self.assertIn(
            'href="/files/7" data-wl-media-open="#media-7"', html
        )  # a link without JS
        self.assertIn('<img src="/files/7/thumb" alt="" loading="lazy">', html)
        self.assertIn('<dialog class="wl-media-dialog" id="media-7"', html)
        self.assertIn('data-src="/files/7/preview"', html)  # loaded when it's opened
        self.assertIn('<form method="dialog">', html)

    def test_remove(self):
        html = self.html([PHOTO_ITEM])
        self.assertIn('action="/reports/1/files/7/remove/"', html)
        self.assertIn('name="version" value="3"', html)
        self.assertIn("Remove seal.jpg", html)
        self.assertNotIn("Remove beach.mp4", self.html([VIDEO_ITEM]))

    def test_video_and_audio(self):
        html = self.html([VIDEO_ITEM, AUDIO_ITEM], card_id="report-media")
        self.assertIn('<video controls preload="none" src="/files/8">', html)
        self.assertIn('id="report-media-8"', html)
        self.assertIn("data-wl-audio", html)
        self.assertNotIn("report-media-9", html)  # audio plays in place

    def test_empty(self):
        self.assertIn("No photos, videos or recordings.", self.html([]))

    def test_blocks_extend(self):
        html = Template(
            '{% extends "wildline_ui/cards/media.html" %}'
            "{% block actions %}<button>Add files</button>{% endblock %}"
            "{% block editor %}<form>upload</form>{% endblock %}"
        ).render(Context({"items": [PHOTO_ITEM]}))
        self.assertIn("<button>Add files</button>", html)
        self.assertIn("<form>upload</form>", html)
        self.assertIn('id="media-7"', html)
