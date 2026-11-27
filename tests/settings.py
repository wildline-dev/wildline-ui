SECRET_KEY = "tests"
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "wildline_ui",
]
# A database only for the record search's tests, which need a model to pick from.
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
STATIC_URL = "static/"
TEMPLATES = [
    {"BACKEND": "django.template.backends.django.DjangoTemplates", "APP_DIRS": True}
]
USE_TZ = True
