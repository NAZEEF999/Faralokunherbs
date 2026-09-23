"""
Local test settings.

Runs the test suite on SQLite instead of the production PostgreSQL
database (which lives on Render and must never be used for tests).
Also forces the locmem email backend so `mail.outbox` is populated.

Usage:
    python manage.py test --settings core.settings_test
"""

from .settings import *  # noqa: F401,F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "test_db.sqlite3",
    }
}

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"