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

# Static files must exist under STATIC_ROOT for WhiteNoise to serve them in
# production. Vercel has no build step for Django, so collect once on import —
# it is idempotent and cheap. Disable with VERCEL_COLLECTSTATIC=0 if you prefer
# to run collectstatic yourself.
if os.getenv('VERCEL_COLLECTSTATIC', '1') == '1':
    import logging
    try:
        from django.core.management import call_command
        call_command('collectstatic', '--noinput', verbosity=0)
    except Exception as exc:
        # Don't take the site down for a collectstatic hiccup, but MAKE IT
        # LOUD: a silently swallowed failure was hiding broken static assets
        # (e.g. 404s for collected files) on the deployed site.
        logging.getLogger(__name__).error(
            'collectstatic FAILED on cold start: %s', exc, exc_info=True)

app = get_wsgi_application()