"""
Vercel serverless entry point.

The Vercel Python runtime imports this module (its ``app`` callable) instead
of running gunicorn, so static files are collected here on a cold start (the
no-op collectstatic keeps the manifest storage happy) and then served through
WhiteNoise, which is already in MIDDLEWARE.

Environment variables (DJANGO_SECRET_KEY, ALLOWED_HOSTS, DATABASE_URL, etc.)
are injected by Vercel from the dashboard — never committed to the repo.
"""
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

from django.core.wsgi import get_wsgi_application  # noqa: E402


def _run_management(command, logger):
    """Run a management command on cold start, never taking the site down."""
    try:
        from django.core.management import call_command
        call_command(command, '--noinput', verbosity=0)
    except Exception as exc:
        # Don't take the site down for a startup hiccup, but MAKE IT
        # LOUD: a silently swallowed failure was hiding broken static
        # assets (e.g. 404s for collected files) on the deployed site.
        logger.error('%s FAILED on cold start: %s', command, exc, exc_info=True)


_logger = None
def _get_logger():
    global _logger
    if _logger is None:
        import logging
        _logger = logging.getLogger(__name__)
    return _logger

# Apply pending migrations (incl. the PHARA product seed data) and collect
# static files. Both are idempotent and cheap; disable with the env vars.
if os.getenv('VERCEL_MIGRATE', '1') == '1':
    _run_management('migrate', _get_logger())
if os.getenv('VERCEL_COLLECTSTATIC', '1') == '1':
    _run_management('collectstatic', _get_logger())

app = get_wsgi_application()