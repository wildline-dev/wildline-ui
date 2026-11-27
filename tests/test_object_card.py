from django import forms
from django.template import Context, Template
from django.template.loader import render_to_string
from django.test import SimpleTestCase

from wildline_ui.cards import Row, parts


class PlaceForm(forms.Form):
    species = forms.CharField(help_text="What kind of animal")
    notes = forms.CharField(widget=forms.Textarea, required=False)


def card(**edit):
    form = PlaceForm(initial={"species": "Gull"})
    return {
        "id": "animal-box",
        "title": "Animal",
        "edit": {
            "action": "/save/",
            "hidden": {"version": 3},
            "label": "Edit animal",
            **edit,
        }
        if edit is not None
        else None,
        "rows": [
            {
                "label": "Species",
                "help": "What kind",
                "text": "Gull",
                "inputs": [form["species"]],
            },
            {"label": "Notes", "text": "", "inputs": [form["notes"]]},
            {"label": "Band", "text": "A12", "hidden": True},
            {"label": "ID", "text": "7"},
        ],
    }


class PartsTests(SimpleTestCase):
    def test_split_keeps_order(self):
        split = parts(card()["rows"])
        self.assertEqual([r.label for r in split.shown], ["Species", "ID"])
        self.assertEqual([r.label for r in split.folded], ["Notes", "Band"])
        # Editing: every row with inputs, and read-only rows with a value.
        self.assertEqual(
            [r.label for r in split.editing], ["Species", "Notes", "Band", "ID"]
        )

    def test_rows_from_objects_and_defaults(self):
        class Thing:
            label = "Name"
            text = None

        row = Row.coerce(Thing())
        self.assertEqual(
            (row.label, row.text, row.inputs, row.hidden), ("Name", "", [], False)
        )
        self.assertTrue(row.folded)


class TemplateTests(SimpleTestCase):
    def render(self, data):
        return render_to_string("wildline_ui/cards/object.html", {"card": data})

    def test_view_and_show_all(self):
        html = self.render(card())
        self.assertIn('<h3 class="h5 wl-card-title">Animal</h3>', html)
        self.assertIn('<dt title="What kind">Species</dt>', html)
        self.assertIn("Show all (2 more)", html)
        self.assertIn("Not answered", html)
        self.assertNotIn("<script", html)

    def test_edit_form(self):
        html = self.render(card())
        self.assertIn('action="/save/"', html)
        self.assertIn('<input type="hidden" name="version" value="3">', html)
        self.assertIn('aria-label="Edit animal"', html)
        self.assertIn('placeholder="Species"', html)
        self.assertIn('title="What kind of animal"', html)
        self.assertIn('rows="2"', html)  # a textarea is short in its row
        self.assertNotIn(" checked", html)
        self.assertIn(" checked", self.render(card(open=True)))

    def test_no_edit(self):
        data = card()
        data["edit"] = None
        html = self.render(data)
        self.assertNotIn("<form", html)
        self.assertNotIn("wl-edit-toggle", html)

    def test_errors_and_custom_template(self):
        form = PlaceForm(data={"species": ""})
        form.is_valid()
        html = self.render(
            {
                "id": "x",
                "title": "X",
                "edit": {"action": "/", "open": True, "errors": ["Give a name."]},
                "rows": [
                    {"label": "Species", "text": "", "inputs": [form["species"]]},
                    {
                        "label": "Where",
                        "text": "here",
                        "template": "wildline_ui/map.html",
                    },
                ],
            }
        )
        self.assertIn("is-invalid", html)
        self.assertIn("This field is required.", html)
        self.assertIn("Give a name.", html)

    def test_empty_card(self):
        html = self.render({"id": "e", "title": "E", "rows": []})
        self.assertIn("Nothing recorded yet.", html)

    def test_assets(self):
        html = Template("{% load wildline_ui %}{% object_card_assets %}").render(
            Context()
        )
        self.assertIn("wildline_ui/css/object-card.css", html)
