# Faralokun Vital Herbs
## Django 5.2

> "Nature's Wisdom, Refined"

Premium herbal wellness platform — products with promotions and cart
checkout, service consultations, a public Health Library (anatomy,
conditions, herbs, wellness), and a staff dashboard with role-based
permissions and 2FA, kept fully separate from Django Admin.

---

## Quick Start

```bash
# 1. Create virtual environment
python -m venv env
source env/bin/activate        # Mac/Linux
env\Scripts\activate           # Windows

# 2. Install all dependencies
pip install -r requirements.txt

# 3. Configure — copy the example and fill in real values
cp .env.example .env

# 4. Run migrations
python manage.py migrate

# 5. Create a developer/superuser account (Django Admin access only —
#    see "Staff & Access" below for how staff dashboard accounts work)
python manage.py createsuperuser

# 6. Start
python manage.py runserver
```

- **Public site**: http://127.0.0.1:8000/
- **Patient portal**: http://127.0.0.1:8000/portal/login/ (optional — booking never requires an account)
- **Staff dashboard**: http://127.0.0.1:8000/dashboard/login/ — the normal interface for staff
- **Django admin**: http://127.0.0.1:8000/admin/ — developer/superuser technical fallback only, not the staff UI

No default credentials are shipped with this project. `createsuperuser` creates a
Django Admin account only — it does **not** by itself grant staff dashboard access.
To create a real staff dashboard account, log into `/dashboard/` as a superuser and
use **Staff & Access** to add one (see below); dashboard access and Django Admin
access are deliberately separate permission systems.

---

## Architecture

```
PUBLIC WEBSITE
  ├── Guest users — full booking + shopping flow, no account needed
  └── Optional patient accounts
          │
          ▼
      /portal/            ← patient's own appointment history, profile, PDF receipts

  /health-library/        ← public Anatomy / Health Conditions / Herbs & Ingredients / Wellness


STAFF / ADMIN
      │
      ▼
  /dashboard/             ← the real staff interface, permission-scoped per section
      ├── Overview            — stats + real appointment calendar
      ├── Appointments        — list/detail, confirm/cancel/complete, conflict-checked
      ├── Patients
      ├── Services
      ├── Categories / Products / Promotions
      ├── Orders              — multi-item cart checkout, staff follow up (no online payment)
      ├── Messages / Inquiries
      ├── Notifications
      ├── Blog
      ├── Health Library      — Anatomy / Conditions / Herbs & Ingredients
      ├── Testimonials
      ├── Subscribers
      ├── Site Settings        — branding, contact, booking notification toggles, SEO, etc.
      ├── Staff & Access       — add/edit staff accounts and their permitted sections
      └── Account & Security   — password change, 2FA setup, recovery codes, active sessions


  /admin/                 ← Django admin, developer/superuser technical fallback only.
                             Staff dashboard accounts never get Django Admin access
                             automatically — the two permission systems are independent.
```

---

## All Pages

| URL | Description |
|-----|-------------|
| `/` | Home |
| `/services/` | Services |
| `/products/` | Herbal products, with active promotions shown automatically |
| `/cart/`, `/checkout/` | Multi-item cart and checkout (no online payment — staff follow up) |
| `/health-library/` | Health Library hub |
| `/health-library/anatomy/` | Anatomy topics |
| `/health-library/conditions/` | Health conditions |
| `/health-library/herbs/` | Herbs & ingredients |
| `/health-library/wellness/` | Wellness articles (Blog posts tagged "Wellness") |
| `/about/` | About + Google Maps |
| `/blog/` | Blog |
| `/contact/` | Contact + Google Maps |
| `/book/` | Book a consultation (guest OR logged-in patient) |
| `/portal/login/` | Patient login |
| `/portal/register/` | Patient registration (optional) |
| `/portal/dashboard/` | Patient dashboard |
| `/portal/appointments/` | Patient's appointment history + PDF receipt |
| `/portal/profile/` | Edit patient profile |
| `/dashboard/login/` | **Staff login** (redirects to 2FA challenge if enabled) |
| `/dashboard/` | **Staff dashboard** — every management section listed above, scoped to what that staff member is permitted to access |
| `/admin/` | Django admin — developer/superuser technical fallback, not the normal staff workflow |

---

## Features

### Products, Promotions & Checkout
- Categories, rich product records (ingredients, benefits, how-to-use, precautions,
  stock, gallery images), and a dedicated Promotion system (percentage or fixed
  discount, scheduled start/end, auto-live/auto-expire)
- The homepage's "Special Offers" band only ever appears while a promotion is
  genuinely live, and disappears automatically when none are — no manual editing
- Session-based multi-item cart and checkout; pricing is always computed
  server-side from the database (including any active promotion), never trusted
  from the browser
- No online payment — an order is saved and staff follow up to arrange payment
  and delivery

### Booking (Consultations)
- **Guest booking** — no account needed, works immediately
- **Logged-in booking** — form pre-fills with patient details, and the appointment is
  linked to the patient's account via `Appointment.patient` (not just email matching)
- There is no public practitioner/healer directory — booking is by service and
  date/time only. Backend availability check at booking time rejects a request
  only if that exact date+time slot is already **confirmed** for someone else;
  a second check runs again when staff confirm it, backed by a database-level
  constraint so two simultaneous confirmations can never both succeed
- Owner/staff booking notifications: independent ON/OFF toggles for email and
  WhatsApp Business API, configured in Site Settings. WhatsApp requires
  `WHATSAPP_BUSINESS_API_TOKEN` and `WHATSAPP_BUSINESS_PHONE_NUMBER_ID` to be set
  on the server — without them it fails gracefully and logs why, rather than
  silently pretending to have sent something. This is separate from the
  pre-filled `wa.me` link, which just opens WhatsApp for a human to send manually
- Email confirmation always sent to the patient (configure SMTP in `.env` for
  production; console backend is used automatically in development)
- Dashboard notification created for staff, with real unread-count badges

### Health Library (`/health-library/`)
- **Anatomy** — explorable body-system topics (function, common issues, further
  info), grouped by system
- **Health Conditions** — overview, causes/risk factors, symptoms, prevention,
  lifestyle tips, general treatment information, and when to seek professional
  care; can link to related herbs
- **Herbs & Ingredients** — traditional uses, active compounds, preparation,
  safety/interactions/precautions; can link to related products
- **Wellness** — reuses the existing Blog system (posts tagged "Wellness"),
  rather than a separate content model
- All content is framed as general education, not medical advice — pages carry
  that disclaimer consistently

### Patient Portal (`/portal/`)
- Optional — patients can book without ever signing up
- Create account → track appointment history → download PDF receipts
- Edit profile (name, phone, address, date of birth)

### Staff Dashboard (`/dashboard/`)
- Access is controlled by a `StaffAccess` role/section system, completely
  independent of Django's `is_staff`/`is_superuser` — see **Staff & Access**
  below. A superuser always has full dashboard access; a staff account only
  sees the sections it's been granted (Products, Orders, Appointments,
  Content, Messages, Settings, Staff)
- Real appointment calendar: month view built from the actual `Appointment`
  table, click a date to see that day's real bookings
- Manage products/categories/promotions, orders, appointments, patients,
  services, blog, the Health Library, testimonials, and subscribers without
  needing Django Admin for normal work
- Site Settings — branding, contact info, hero content, booking notification
  toggles, SEO fields, etc.; changes propagate to the public site immediately
- Medical notes are only ever visible here, to authenticated staff — never in
  WhatsApp messages, public pages, or patient-facing confirmations

### Staff & Access
- The owner (or a superuser) can create staff accounts and assign a role
  (Owner, Product Manager, Content Manager, Order Manager, Appointment
  Manager, or Custom with hand-picked sections) directly from
  `/dashboard/staff/`
- Creating or editing a staff account **never** sets `is_staff` or
  `is_superuser` — dashboard access and Django Admin access are two separate
  systems by design, so a staff account can never accidentally end up with
  technical Django Admin privileges

### Account & Security
- Self-service password change from `/dashboard/account-security/`
- TOTP-based 2FA (Google Authenticator, Microsoft Authenticator, Authy, or
  any standard authenticator app) — QR code + manual key setup, hashed
  one-time recovery codes shown exactly once, and a genuine two-step login
  (a password alone can't reach the dashboard once 2FA is enabled)
- "Log out other sessions" support
- Self-service "forgot password" flow for staff accounts, using Django's own
  token generator (one-time, expiring reset links)

### Email Notifications
Configure in `.env`:
```
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-app-password
```
The email backend switches automatically: console backend (prints to terminal) when
`DEBUG=True`, SMTP when `DEBUG=False`, unless `EMAIL_BACKEND` is set explicitly.

### WhatsApp Business API (owner booking notifications)
Configure in `.env`:
```
WHATSAPP_BUSINESS_API_TOKEN=your_token
WHATSAPP_BUSINESS_PHONE_NUMBER_ID=your_phone_number_id
```
Server-side only — never exposed to templates, JS, or the dashboard UI. Without
both set, WhatsApp booking notifications are skipped with a clear log message
and a visible in-dashboard notification, even if turned on in Site Settings.

### Cloudinary Images
Set in `.env`:
```
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```
Sign up free at cloudinary.com. Service, product, product gallery, blog, and
Health Library (anatomy/condition/herb) images can all be uploaded directly
from `/dashboard/`.

### PostgreSQL (Production)
Set in `.env`:
```
DATABASE_URL=postgresql://user:password@host:5432/dbname
```
SQLite is used automatically for local development when `DATABASE_URL` is unset.

---

## Testing

```bash
python manage.py test
```

Runs the full automated test suite (staff auth and permissions, 2FA, password reset,
guest/registered booking, appointment conflict handling, promotions/cart/checkout,
Health Library, calendar behavior, notification/message read-state, SiteSettings
propagation, and more) against a fresh, disposable test database — it never touches
your real `db.sqlite3` or production data.

---

## Stack
- **Backend**: Django 5.2.5
- **Frontend**: Tailwind CSS v4 (CDN) for the public site; hand-styled dashboard
- **2FA**: pyotp (TOTP) + qrcode
- **Images**: Cloudinary
- **PDF**: xhtml2pdf
- **Database**: SQLite (dev) → PostgreSQL via `DATABASE_URL` (prod)
- **Static files**: WhiteNoise (`static/` is source; `staticfiles/` is generated by
  `collectstatic` during deployment and isn't part of this repository)
- **Fonts**: Cormorant Garamond + DM Sans

---

## Deployment (PWA, Push, SMTP, HTTPS)

### HTTPS

The Faralokun Vital Herbs Dashboard is a PWA: service worker, manifest and Web Push all require a secure context. Local development on `http://127.0.0.1` works without HTTPS. Production must be behind HTTPS — any reverse proxy, Load Balancer, or PaaS (Render, Railway, Fly.io) that terminates TLS is fine; the codebase sets `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')` automatically in production so Django correctly identifies the connection.

### Environment variables

Set these in your production `.env`. **Never commit the real `.env` to source control.**

| Variable | Purpose |
|---|---|
| `EMAIL_BACKEND` | Set to `django.core.mail.backends.smtp.EmailBackend` in production (default: `console` in DEBUG, `smtp` when DEBUG is False). |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS` | SMTP credentials — for Gmail: `smtp.gmail.com`, port `587`, `True`. |
| `DEFAULT_FROM_EMAIL` | Sender address shown on alerts, e.g. `Faralokun Vital Herbs <you@yourdomain.com>`. |
| `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`, `VAPID_CLAIMS_EMAIL` | Web Push delivery; generate once with `python manage.py generate_vapid_keys` and paste into `.env`. |
| `WHATSAPP_BUSINESS_API_TOKEN`, `WHATSAPP_BUSINESS_PHONE_NUMBER_ID` | Optional: automatic WhatsApp booking alerts. |
| `WHATSAPP_API_VERSION` | Override when Meta deprecates a Graph API version (default `v20.0`). |
| `CLOUDINARY_*` | Cloudinary image CDN credentials. |
| `DATABASE_URL` | PostgreSQL connection string for production. |

### Post-deploy steps

```bash
python manage.py migrate               # apply any new migrations
python manage.py collectstatic --noinput # generate the staticfiles/ bundle
```

**Service Worker note:** The manifest (`/dashboard/manifest.webmanifest`) and SW (`/dashboard/sw.js`) are served publicly (no login) so installability works. The SW only caches `/static/` assets; it never caches dashboard HTML, so sensitive data is never stored offline.
