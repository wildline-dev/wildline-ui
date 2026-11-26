# wildline-ui

Shared low-bandwidth styling for Wildline Django apps: a slim Bootstrap 5.3 build (about 7.2 KB gzipped, no JavaScript) and template tags that inline it, so each page loads in a single request.

## Use it in an app

```sh
uv add "wildline-ui @ git+https://github.com/wildline-dev/wildline-ui@v0.1.0"
```

Add `"wildline_ui"` to `INSTALLED_APPS` (it needs `django.contrib.staticfiles`), then in your base template:

```django
{% load wildline_ui %}
<head>
  ...
  {% wildline_css %}
</head>
```

`{% inline_static "path/in/static.css" %}` inlines any other static file the same way. Use it only for files from the codebase.

## Change the styles

The compiled CSS in `src/wildline_ui/static/wildline_ui/css/` is committed, so apps don't need Node. To add a Bootstrap component or utility, edit `assets/scss/wildline-slim.scss`, then:

```sh
npm ci
npm run build:css
```

Bump `version` in `pyproject.toml`, tag the release (e.g. `v0.2.0`), and update the tag in each app.

## Tests

```sh
DJANGO_SETTINGS_MODULE=tests.settings uv run python -m django test --pythonpath=.
```
