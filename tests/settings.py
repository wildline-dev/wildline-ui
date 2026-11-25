SECRET_KEY = "tests"
INSTALLED_APPS = ["django.contrib.staticfiles", "wildline_ui"]
STATIC_URL = "static/"
TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates", "APP_DIRS": True}]
USE_TZ = True
