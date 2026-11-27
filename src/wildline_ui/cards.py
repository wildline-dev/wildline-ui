"""The Object card (#5): a record's fields from a dict the view builds, edited in place.

The card only displays. The view builds the dict, takes the POST, validates its own forms and
renders the card again (with ``edit["open"]`` to keep it in edit mode after errors). The dict:

    card = {
        "id": "report-box",               # unique on the page
        "title": "Report",
        "edit": {                          # None (or left out): no pencil
            "action": url,                 # the form posts here
            "hidden": {"version": 7},      # extra hidden inputs
            "multipart": False,            # True when an input takes files
            "label": "Edit report",        # the pencil's name for screen readers
            "open": False,                 # show the form, such as after errors
            "errors": [],                  # messages above the inputs (a form's non-field errors)
            "text": "",                    # a text pencil ("Edit"), for apps without Bootstrap Icons
        },
        "rows": [
            {
                "label": "Species",
                "help": "Shown on hovering the label",
                "text": "Gull",            # empty: "Not answered"
                "hidden": False,           # hidden and empty rows fold under "Show all"
                "wide": False,             # no label, the card's full width
                "template": None,          # a custom display, given row and value
                "value": None,             # for that template
                "inputs": [bound_field],   # its inputs while editing; [] keeps it read-only
                "related": {               # a related record (a foreign key): an inset box,
                    "url": "/contacts/4/", # with a button to its page
                    "label": "Open contact",
                },
            },
        ],
    }

Rows can be dicts or any object with those attributes; anything left out takes the default.
"""

from dataclasses import dataclass, field, fields

from django.forms import Media

OBJECT_CARD_MEDIA = Media(
    css={"all": ["wildline_ui/css/cards.css", "wildline_ui/css/object-card.css"]}
)


@dataclass
class Row:
    label: str = ""
    help: str = ""
    text: str = ""
    hidden: bool = False
    wide: bool = False
    template: str | None = None
    value: object = None
    inputs: list = field(default_factory=list)
    related: dict | None = None

    @classmethod
    def coerce(cls, row):
        if isinstance(row, cls):
            return row
        get = (
            row.get
            if isinstance(row, dict)
            else lambda name, default: getattr(row, name, default)
        )
        values = {f.name: get(f.name, None) for f in fields(cls)}
        values = {name: value for name, value in values.items() if value is not None}
        values["inputs"] = list(values.get("inputs") or ())
        return cls(**values)

    @property
    def empty(self):
        return self.text in ("", [], ())

    @property
    def folded(self):
        return self.hidden or self.empty


@dataclass
class Parts:
    shown: list  # rows with a value that aren't hidden
    folded: list  # hidden or empty: under "Show all (N more)"
    editing: list  # rows the form shows: with inputs, or read-only with a value


def parts(rows):
    """Split a card's rows for display and editing, keeping their order."""
    rows = [Row.coerce(row) for row in rows or ()]
    return Parts(
        shown=[row for row in rows if not row.folded],
        folded=[row for row in rows if row.folded],
        editing=[row for row in rows if row.inputs or not row.empty],
    )


def inline_input(bound_field):
    """A form field's input alone, small, for editing a value where it's shown: its label is the
    placeholder and the name screen readers read, its help text the tooltip."""
    widget = bound_field.field.widget
    input_type = getattr(widget, "input_type", "")
    if input_type == "checkbox":
        css = "form-check-input"
    elif input_type == "select" or widget.__class__.__name__.endswith("Select"):
        css = "form-select form-select-sm"
    else:
        css = "form-control form-control-sm"
    if bound_field.errors:
        css += " is-invalid"
    existing = widget.attrs.get("class")
    attrs = {
        "class": f"{existing} {css}" if existing else css,
        "aria-label": bound_field.label,
    }
    if input_type not in ("checkbox", "file", "select") and not hasattr(
        widget, "widgets"
    ):
        attrs["placeholder"] = bound_field.label
    if bound_field.help_text:
        attrs["title"] = bound_field.help_text
    if (
        widget.__class__.__name__ == "Textarea"
        and str(widget.attrs.get("rows")) == "10"
    ):
        attrs["rows"] = (
            2  # Django's default is 10: short in a row; drag its corner for more
        )
    return bound_field.as_widget(attrs=attrs)
