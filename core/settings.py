import os
from pathlib import Path
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

# Local secrets live in .env.local (git-ignored) and load first, so the
# stripped, deployment-safe .env (variable names only) never overwrites a
# real local value. On a server (Vercel/Render) env vars come from the
# platform itself and neither file is needed.
load_dotenv(BASE_DIR / '.env.local')
load_dotenv(BASE_DIR / '.env')

# DEBUG defaults to False so a missing/misconfigured .env never accidentally
# ships to production with debug mode on. Set DEBUG=True in your local .env.
DEBUG = os.getenv('DEBUG', 'False') == 'True'

_FALLBACK_SECRET_KEY = 'fallback-dev-key-change-in-production'
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', '').strip() or _FALLBACK_SECRET_KEY
if not DEBUG and SECRET_KEY == _FALLBACK_SECRET_KEY:
    raise ImproperlyConfigured(
        'DJANGO_SECRET_KEY is not set. Refusing to run with DEBUG=False and the '
        'fallback development secret key — set DJANGO_SECRET_KEY in your environment.'
    )

ALLOWED_HOSTS = [h.strip() for h in os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') if h.strip()]

# ── APPS ─────────────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    'unfold',
    'unfold.contrib.filters',
    'unfold.contrib.forms',
    'unfold.contrib.inlines',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'cloudinary',
    'cloudinary_storage',
    'rest_framework',
    'corsheaders',
    'django_filters',
    'api',
    'accounts',
    'dashboard',
    'health',
]
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'api.context_processors.site_settings',
                'dashboard.context_processors.dashboard_nav',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# ── DATABASE ─────────────────────────────────────────────────────────────────
DATABASE_URL = os.getenv('DATABASE_URL', '').strip()
if DATABASE_URL:
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600, ssl_require=not DEBUG)
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
            'OPTIONS': {
                'timeout': 30,
            }
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Lagos'
USE_I18N = True
USE_TZ = True

# ── STATIC & MEDIA ───────────────────────────────────────────────────────────
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── LOGGING ──────────────────────────────────────────────────────────────────
# Without this, exceptions caught and logged in try/except blocks (email
# sending, WhatsApp link generation, etc.) had nowhere reliable to go.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {'format': '[{asctime}] {levelname} {name}: {message}', 'style': '{'},
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'simple'},
    },
    'root': {'handlers': ['console'], 'level': 'INFO'},
    'loggers': {
        'django': {'handlers': ['console'], 'level': 'WARNING', 'propagate': False},
        'api':       {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
        'dashboard': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
        'accounts':  {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
    },
}

# ── EMAIL ─────────────────────────────────────────────────────────────────────
# These were present in .env but never read here, so appointment confirmation
# and status-update emails were silently falling back to Django's default SMTP
# backend pointed at localhost:25, which always fails and gets swallowed by the
# try/except blocks in email_service.py.
_default_email_backend = ('django.core.mail.backends.console.EmailBackend' if DEBUG
                           else 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_BACKEND         = os.getenv('EMAIL_BACKEND', _default_email_backend)
EMAIL_HOST            = os.getenv('EMAIL_HOST', '')
EMAIL_PORT            = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_HOST_USER       = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD   = os.getenv('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS         = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
DEFAULT_FROM_EMAIL    = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@phara.ng')

# ── ADMIN / NOTIFICATION E-MAIL ─────────────────────────────────────────────
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', '').strip()

# ── WEB PUSH NOTIFICATIONS (VAPID) ──────────────────────────────────────────
# Server-side VAPID keys for the Web Push protocol (RFC 8292). The PRIVATE key
# and email subject stay server-only and are never sent to the browser; only
# VAPID_PUBLIC_KEY is exposed to the dashboard JS. Generate a pair with:
#   python -m venv .pushvenv  (pywebpush must be installed on the server)
#   python -c "from pywebpush import generate_vapid_keys; import json; print(json.dumps(generate_vapid_keys()))"
# then put the keys in .env (VAPID_PUBLIC_KEY / VAPID_PRIVATE_KEY).
VAPID_PUBLIC_KEY   = os.getenv('VAPID_PUBLIC_KEY', '').strip()
VAPID_PRIVATE_KEY  = os.getenv('VAPID_PRIVATE_KEY', '').strip()
VAPID_CLAIMS_EMAIL = os.getenv('VAPID_CLAIMS_EMAIL', ADMIN_EMAIL).strip()

# ── WHATSAPP BUSINESS PLATFORM (Cloud API) ──────────────────────────────────
# Server-side only -- never exposed to templates, JS, or the dashboard UI.
# Both must be set for automatic (non-wa.me-link) WhatsApp booking
# notifications to actually send; api/whatsapp_service.py fails gracefully
# and logs clearly when either is missing, rather than pretending to send.
WHATSAPP_BUSINESS_API_TOKEN       = os.getenv('WHATSAPP_BUSINESS_API_TOKEN', '').strip()
WHATSAPP_BUSINESS_PHONE_NUMBER_ID = os.getenv('WHATSAPP_BUSINESS_PHONE_NUMBER_ID', '').strip()
# Meta bumps Graph API versions periodically; old ones stop being served.
# Override via WHATSAPP_API_VERSION in .env when a new version ships and the
# default below eventually falls out of support.
WHATSAPP_API_VERSION              = os.getenv('WHATSAPP_API_VERSION', 'v20.0').strip()

# ── CLOUDINARY ───────────────────────────────────────────────────────────────
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.getenv('CLOUDINARY_CLOUD_NAME'),
    'API_KEY': os.getenv('CLOUDINARY_API_KEY'),
    'API_SECRET': os.getenv('CLOUDINARY_API_SECRET'),
}
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# ── CORS ─────────────────────────────────────────────────────────────────────
# Allow-all origins is unnecessarily permissive for a server-rendered site with
# no separate public API consumers. Restrict to explicit trusted origins,
# configurable via env for whichever frontends actually need cross-origin access.
_cors_origins = [o.strip() for o in os.getenv('CORS_ALLOWED_ORIGINS', '').split(',') if o.strip()]
CORS_ALLOW_ALL_ORIGINS = DEBUG and not _cors_origins
CORS_ALLOWED_ORIGINS = _cors_origins

# ── PRODUCTION SECURITY HARDENING ────────────────────────────────────────────
# All controlled through env vars so local development (DEBUG=True, plain
# http://localhost) isn't affected — these only bite once DEBUG=False.
CSRF_TRUSTED_ORIGINS = [o.strip() for o in os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',') if o.strip()]

if not DEBUG:
    SECURE_SSL_REDIRECT        = os.getenv('SECURE_SSL_REDIRECT', 'True') == 'True'
    # Almost every PaaS host (Render, Railway, Fly.io, etc.) terminates TLS at
    # their edge and forwards plain HTTP internally, setting this header to
    # tell us the original request was HTTPS. Without this, Django can't see
    # that and SECURE_SSL_REDIRECT causes an infinite redirect loop.
    SECURE_PROXY_SSL_HEADER    = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE      = True
    CSRF_COOKIE_SECURE         = True
    SECURE_HSTS_SECONDS        = int(os.getenv('SECURE_HSTS_SECONDS', '31536000'))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    # Preload is opt-in: submitting a brand-new or staging domain to the HSTS
    # preload list can lock out HTTPS-only users prematurely. Enable explicitly
    # once the production domain is final.
    SECURE_HSTS_PRELOAD        = os.getenv('SECURE_HSTS_PRELOAD', 'False') == 'True'
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS            = 'DENY'

# ── MESSAGES ─────────────────────────────────────────────────────────────────
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG:   'alert-secondary',
    messages.INFO:    'alert-info',
    messages.SUCCESS: 'alert-success',
    messages.WARNING: 'alert-warning',
    messages.ERROR:   'alert-danger',
}



from django.templatetags.static import static
from django.urls import reverse_lazy

UNFOLD = {
    "SITE_TITLE": "Faralokun Vital Herbs",
    "SITE_HEADER": "Faralokun Vital Herbs Admin",
    "SITE_SUBHEADER": "Faralokun Vital Herbs Wellness",
    "SITE_DROPDOWN": [],
    "SITE_URL": "/",
    "SITE_ICON": None,
    "SITE_LOGO": None,
    "SITE_SYMBOL": "ecg_heart",
    "SITE_FAVICONS": [],
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "SHOW_BACK_BUTTON": True,
    "ENVIRONMENT": "api.utils.environment_callback",
    "ENVIRONMENT_TITLE_PREFIX": True,
    "DASHBOARD_CALLBACK": None,

    # Keep this if you want forced dark mode.
    # Remove it later if you want Unfold's theme switcher.
    "THEME": "dark",

    "LOGIN": {
        "image": None,
        "redirect_after": "/admin/",
    },

    "STYLES": [
        lambda request: static("css/unfold-custom.css"),
    ],
    "SCRIPTS": [
        lambda request: static("js/unfold-custom.js"),
    ],

    # Use valid, real values here.
    "COLORS": {
        "base": {
            "50":  "240 253 244",
            "100": "220 252 231",
            "200": "187 247 208",
            "300": "134 239 172",
            "400": "74 222 128",
            "500": "34 197 94",
            "600": "22 163 74",
            "700": "21 128 61",
            "800": "20 83 45",
            "900": "17 24 39",
            "950": "5 46 22",
        },
        "font": {
            "subtle-light": "107 114 128",
            "subtle-dark": "156 163 175",
            "default-light": "17 24 39",
            "default-dark": "243 244 246",
            "important-light": "0 0 0",
            "important-dark": "255 255 255",
        },
        "primary": {
            "50":  "240 253 244",
            "100": "220 252 231",
            "200": "187 247 208",
            "300": "134 239 172",
            "400": "74 222 128",
            "500": "34 197 94",
            "600": "22 163 74",
            "700": "21 128 61",
            "800": "20 83 45",
            "900": "17 24 39",
            "950": "5 46 22",
        },
    },

    "EXTENSIONS": {
        "modeltranslation": {
            "flags": {},
        },
    },

    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": "Dashboard",
                "separator": False,
                "collapsible": True,
                "items": [
                    {
                        "title": "Dashboard",
                        "icon": "dashboard",
                        "link": reverse_lazy("admin:index"),
                        "permission": lambda request: request.user.is_staff,
                    },
                ],
            },
            {
                "title": "Clinic",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Appointments",
                        "icon": "calendar_month",
                        "link": reverse_lazy("admin:api_appointment_changelist"),
                        "badge": "api.utils.appointment_badge",
                    },
                    {
                        "title": "Inquiries",
                        "icon": "mail",
                        "link": reverse_lazy("admin:api_inquiry_changelist"),
                        "badge": "api.utils.inquiry_badge",
                    },
                    {
                        "title": "Notifications",
                        "icon": "notifications",
                        "link": reverse_lazy("admin:api_notification_changelist"),
                        "badge": "api.utils.notification_badge",
                    },

                    
                ],
            },
            {
                "title": "Catalogue",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Services",
                        "icon": "healing",
                        "link": reverse_lazy("admin:api_service_changelist"),
                    },
                    {
                        "title": "Product Categories",
                        "icon": "category",
                        "link": reverse_lazy("admin:api_productcategory_changelist"),
                    },
                    {
                        "title": "Products",
                        "icon": "eco",
                        "link": reverse_lazy("admin:api_product_changelist"),
                    },
                    {
                        "title": "Promotions",
                        "icon": "sell",
                        "link": reverse_lazy("admin:api_promotion_changelist"),
                    },
                    {
                        "title": "Orders",
                        "icon": "shopping_bag",
                        "link": reverse_lazy("admin:api_order_changelist"),
                        "badge": "api.utils.order_badge",
                    },
                ],
            },
            {
                "title": "Content",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Blog Posts",
                        "icon": "article",
                        "link": reverse_lazy("admin:api_blogpost_changelist"),
                    },
                    {
                        "title": "Testimonials",
                        "icon": "star",
                        "link": reverse_lazy("admin:api_testimonial_changelist"),
                    },
                    {
                        "title": "Subscribers",
                        "icon": "email",
                        "link": reverse_lazy("admin:api_subscriber_changelist"),
                    },
                ],
            },
            {
                "title": "Patients",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Patient Profiles",
                        "icon": "people",
                        "link": reverse_lazy("admin:accounts_patientprofile_changelist"),
                    },
                ],
            },
            {
                "title": "Settings",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Site Settings",
                        "icon": "settings",
                        "link": reverse_lazy("admin:api_sitesettings_changelist"),
                    },
                    {
                        "title": "Users",
                        "icon": "manage_accounts",
                        "link": reverse_lazy("admin:auth_user_changelist"),
                    },
                ],
            },
            {
                "title": "Tools",
                "separator": True,
                "collapsible": False,
                "items": [
                    {
                        "title": "Appointment Calendar",
                        "icon": "calendar_view_month",
                        "link": "/admin-tools/calendar/",
                    },
                    {
                        "title": "WhatsApp Templates",
                        "icon": "chat",
                        "link": "/admin-tools/wa-templates/",
                    },
                    {
                        "title": "View Website",
                        "icon": "open_in_new",
                        "link": "/",
                        "external_link": True,
                    },
                ],
            },
        ],
    },

    "TABS": [],
}