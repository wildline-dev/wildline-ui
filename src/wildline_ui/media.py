"""Photos, videos and recordings in the shared Media and Audio cards (#6, #7).

The cards take a list of item dicts that the view builds, so they know nothing about any
app's models. ``item()`` builds one with the defaults filled in:

``key``            unique within the card, for the viewer's id (#<card_id>-<key>)
``kind``           "photo", "video" or "audio"
``name``           the file's name, for labels and alt text
``url``            the original
``thumbnail_url``  a small square image for the grid (photos; a play icon shows without one)
``preview_url``    a larger image for the full-screen viewer (photos; the original without one)
``caption``        a line under or above it, such as "seal.jpg · 9:10 PM · Sam"
``duration``       seconds (audio): over 10 minutes, the player skips drawing a waveform
``error``          what the player says if the audio won't load
``remove``         {"action": url, "hidden": {name: value}} for a Remove button, or None
"""

from django.forms import Media


PHOTO, VIDEO, AUDIO = "photo", "video", "audio"

# The audio player (#7) and the Media card's full-screen viewer (#6). The viewer's page needs
# both, since the Media card shows recordings as players.
AUDIO_MEDIA = Media(
    css={"all": ["wildline_ui/css/cards.css", "wildline_ui/css/media.css"]},
    js=[
        "wildline_ui/vendor/wavesurfer/wavesurfer.min.js",
        "wildline_ui/js/audio-player.js",
    ],
)
VIEWER_MEDIA = AUDIO_MEDIA + Media(js=["wildline_ui/js/media-viewer.js"])


def item(key, kind, url, name="", **extra):
    return {
        "key": key,
        "kind": kind,
        "url": url,
        "name": name,
        "thumbnail_url": "",
        "preview_url": "",
        "caption": "",
        "duration": None,
        "error": "",
        "remove": None,
        **extra,
    }


def remove(action, **hidden):
    """An item's Remove button: posts the hidden fields (and the CSRF token) to action."""
    return {"action": action, "hidden": hidden}
