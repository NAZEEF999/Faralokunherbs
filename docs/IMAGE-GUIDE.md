# Image Guide — Faralokun Vital Herbs

This lists every placeholder image the redesigned templates reference. Drop a
correctly-named file into the exact path below and it appears automatically —
no template or code changes needed.

## Current Brand Assets

- **`static/img/fv-mark.png`** — the Faralokun Vital Herbs brand mark
  (transparent background), used as the fallback logo everywhere one is
  needed: navbar, footer, hero card, favicon, and social-share image
  fallback. A real logo can be uploaded in Website Settings (dashboard) at
  any time, which will override this fallback automatically wherever
  `site.logo` is checked in templates.
- **`static/img/FVH.jpeg`** — the source logo (white background, 1024×1024)
  that `fv-mark.png`, `icon-192.png`, `icon-512.png` and
  `icon-maskable-512.png` were generated from. Keep it in the repo so the
  assets can be regenerated.
- **`static/img/logo.jpeg`** — a leftover file from before the Faralokun
  rebrand. It is not referenced anywhere in the current codebase (confirmed
  by search) and is not the Faralokun logo. Left in place; safe to delete
  whenever convenient, but nothing depends on it either way.

All paths are relative to the project root. All are served via Django's
`{% static %}` tag, so once the file exists at that exact path, it just works
— no `collectstatic` step needed in local development (`runserver` serves
`static/` directly), though production deployments should still run
`python manage.py collectstatic` as usual.

If a file is missing, the page still renders correctly — the section falls
back to a soft brand-colored gradient panel instead of a broken image icon.

---

## 1. Home Page (`templates/home/index.html`)

### `static/img/hero-home.jpg`
- **Section:** Hero, background layer behind the dark green overlay
- **Recommended size:** 1600 × 1000px
- **Aspect ratio:** 16:10 (landscape)
- **Depicts:** Traditional/herbal healing atmosphere — mortar and pestle,
  herbs, calm treatment setting. Shown at low opacity (~22%) behind a dark
  green gradient, so it should read well even quite dark/muted; avoid
  busy or high-contrast images that will fight the overlay text.

### `static/img/about-main.jpg`
- **Section:** "About Preview" (story section, left image)
- **Recommended size:** 1000 × 750px
- **Aspect ratio:** 4:3
- **Depicts:** A real photo representing the practice — herbal preparation
  space, natural remedies, or a consultation setting. Should look warm and
  trustworthy, not stock-photo generic.

### Service / Product / Blog cards on the home page
Reuse the same placeholder files defined in their own sections below —
`service-placeholder.jpg`, `product-placeholder.jpg`, `blog-placeholder.jpg`.
No separate home-page-specific files needed; each card already prefers the
real uploaded image from the database (via the dashboard) and only falls
back to these placeholders when an individual Service/Product/BlogPost has
no image uploaded yet.

---

## 2. About Page (`templates/about/index.html`)

### `static/img/about-hero.jpg`
- **Section:** Hero band background (behind "About Faralokun Vital Herbs" heading)
- **Recommended size:** 1600 × 600px
- **Aspect ratio:** ~8:3 (wide banner)
- **Depicts:** Same visual family as the home hero — subtle, textural,
  shown at ~18% opacity under a dark green gradient. A close-up of herbs,
  mortar and pestle, or traditional healing tools works well.

### `static/img/about-main.jpg`
Same file as the home page's About Preview section (see above) — reused
directly, not a separate image.

---

## 3. Services Page

### `static/img/services-hero.jpg`
- **Path:** `static/img/services-hero.jpg`
- **Page:** `templates/services/list.html`
- **Section:** Hero band background
- **Recommended size:** 1600 × 600px
- **Aspect ratio:** ~8:3
- **Depicts:** Same subtle-banner treatment as `about-hero.jpg` — healing
  service imagery (herbal remedies, consultation setting).

### `static/img/service-placeholder.jpg`
- **Path:** `static/img/service-placeholder.jpg`
- **Pages:** `templates/services/list.html` (card grid), `templates/services/detail.html` (hero image), `templates/home/index.html` (featured services)
- **Section:** Fallback image for any individual `Service` record that has
  no image uploaded via the dashboard yet
- **Recommended size:** 800 × 600px
- **Aspect ratio:** 4:3
- **Depicts:** A generic, appropriate stand-in for a healing service —
  herbs, treatment tools, or a calm consultation setting. Since this is a
  fallback shown whenever ANY service lacks a photo, keep it generic
  enough to suit multiple service types (not, e.g., specific to one
  named treatment).

---

## 4. Products Page

### `static/img/products-hero.jpg`
- **Path:** `static/img/products-hero.jpg`
- **Page:** `templates/products/list.html`
- **Section:** Hero band background
- **Recommended size:** 1600 × 600px
- **Aspect ratio:** ~8:3
- **Depicts:** Herbal products, bottles, natural remedies — same subtle
  banner treatment as other hero images.

### `static/img/product-placeholder.jpg`
- **Path:** `static/img/product-placeholder.jpg`
- **Pages:** `templates/products/list.html`, `templates/products/detail.html`, `templates/home/index.html`
- **Section:** Fallback image for any individual `Product` record with no
  image uploaded via the dashboard yet
- **Recommended size:** 800 × 800px
- **Aspect ratio:** 1:1 (square)
- **Depicts:** A generic herbal product bottle/jar/packet — neutral enough
  to stand in for any product category until a real photo is uploaded.

---

## 5. Blog Page

### `static/img/blog-hero.jpg`
- **Path:** `static/img/blog-hero.jpg`
- **Page:** `templates/blog/list.html`
- **Section:** Hero band background
- **Recommended size:** 1600 × 600px
- **Aspect ratio:** ~8:3
- **Depicts:** Reading/writing/healing-wisdom atmosphere — books, herbs,
  a calm study/writing setting.

### `static/img/blog-placeholder.jpg`
- **Path:** `static/img/blog-placeholder.jpg`
- **Pages:** `templates/blog/list.html`, `templates/blog/detail.html`, `templates/home/index.html`
- **Section:** Fallback cover image for any individual `BlogPost` with no
  image uploaded via the dashboard yet
- **Recommended size:** 900 × 675px
- **Aspect ratio:** 4:3
- **Depicts:** A generic "healing wisdom" editorial image — herbs, books,
  or a calm natural setting appropriate for any article topic.

---

## 6. Contact Page

### `static/img/contact-hero.jpg`
- **Path:** `static/img/contact-hero.jpg`
- **Page:** `templates/contact/index.html`
- **Section:** Hero band background
- **Recommended size:** 1600 × 600px
- **Aspect ratio:** ~8:3
- **Depicts:** Same subtle-banner treatment — an inviting, approachable
  image evoking communication/welcome (e.g. an open doorway, a warm
  reception space).

---

## Quick Reference Table

| Filename | Path | Recommended Size | Aspect Ratio |
|---|---|---|---|
| `hero-home.jpg` | `static/img/hero-home.jpg` | 1600×1000 | 16:10 |
| `about-hero.jpg` | `static/img/about-hero.jpg` | 1600×600 | ~8:3 |
| `about-main.jpg` | `static/img/about-main.jpg` | 1000×750 | 4:3 |
| `services-hero.jpg` | `static/img/services-hero.jpg` | 1600×600 | ~8:3 |
| `service-placeholder.jpg` | `static/img/service-placeholder.jpg` | 800×600 | 4:3 |
| `products-hero.jpg` | `static/img/products-hero.jpg` | 1600×600 | ~8:3 |
| `product-placeholder.jpg` | `static/img/product-placeholder.jpg` | 800×800 | 1:1 |
| `blog-hero.jpg` | `static/img/blog-hero.jpg` | 1600×600 | ~8:3 |
| `blog-placeholder.jpg` | `static/img/blog-placeholder.jpg` | 900×675 | 4:3 |
| `contact-hero.jpg` | `static/img/contact-hero.jpg` | 1600×600 | ~8:3 |

---

## A note on real content images

The placeholders above are only ever *fallbacks*. The real, correct way to
add images for a specific Service, Product, or Blog post is to upload it
directly through `/dashboard/` when creating or editing that record — those
go through Cloudinary and are unrelated to this static placeholder system.
The files above only matter for the shared hero banners and for records
that don't have their own image yet.
