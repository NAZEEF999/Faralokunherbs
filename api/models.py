from django.db import models
from django.utils.text import slugify
from django.utils import timezone
from cloudinary.models import CloudinaryField


# ── SITE SETTINGS (one row — the whole site config) ──────────────────────────
class SiteSettings(models.Model):
    site_name          = models.CharField(max_length=100, default='Faralokun Vital Herbs')
    tagline            = models.CharField(max_length=200, default="Nature's Wisdom, Refined")
    logo               = CloudinaryField('logo', folder='phara/branding', blank=True, null=True)
    favicon            = CloudinaryField('favicon', folder='phara/branding', blank=True, null=True)
    logo_contains_name = models.BooleanField(
        default=False,
        help_text='Check if your uploaded logo already includes the company name (e.g. a wordmark). '
                   'The header will then show the logo alone without repeating the site name.')
    primary_color      = models.CharField(max_length=7, default='#3A7D44')
    secondary_color    = models.CharField(max_length=7, default='#C49A3C')
    accent_color       = models.CharField(max_length=7, default='#B0683A')
    contact_email      = models.EmailField(blank=True, default='')
    contact_phone      = models.CharField(max_length=20, blank=True, default='')
    contact_phone2     = models.CharField(max_length=20, blank=True)
    whatsapp_number    = models.CharField(max_length=20, blank=True, default='',
                                          help_text='Digits only e.g. 2348062952711')
    whatsapp_greeting  = models.TextField(default='Hello Faralokun Vital Herbs! I would like to know more about your herbal wellness products.')
    address            = models.TextField(blank=True, default='')
    city               = models.CharField(max_length=100, default='Lagos')
    country            = models.CharField(max_length=100, default='Nigeria')
    hero_headline      = models.CharField(max_length=200, default='Timeless Wellness, Naturally Refined')
    hero_subheadline   = models.TextField(default='Premium herbal remedies crafted with ancient wisdom and modern care.')
    hero_cta_primary   = models.CharField(max_length=100, default='Shop Herbal Products')
    hero_cta_secondary = models.CharField(max_length=100, default='Book a Consultation')
    hero_video_url     = models.CharField(max_length=300, blank=True,
                                          help_text='YouTube / embeddable video URL, or a local file path '
                                                    'like /static/vid/0917.mp4')

    # ── Dedicated promotional video section (homepage, below testimonials) ──
    promo_video_enabled      = models.BooleanField(
        default=False, help_text='Show the promotional video section on the homepage.')
    promo_video_title        = models.CharField(max_length=200, blank=True)
    promo_video_description  = models.TextField(blank=True)
    promo_video_url          = models.CharField(max_length=300, blank=True,
                                                 help_text='YouTube / embeddable video URL, or a local file '
                                                           'path like /static/vid/0917.mp4')
    promo_video_poster       = CloudinaryField('promo video poster', folder='phara/branding',
                                               blank=True, null=True)
    promo_video_cta_label    = models.CharField(max_length=100, blank=True)
    promo_video_cta_url      = models.CharField(max_length=200, blank=True)

    VIDEO_FILE_EXTENSIONS = ('.mp4', '.m4v', '.webm', '.mov', '.ogv')

    def _url_is_file(self, url):
        u = (url or '').strip()
        return bool(u) and (u.startswith('/') or u.lower().endswith(self.VIDEO_FILE_EXTENSIONS))

    @property
    def hero_video_is_file(self):
        return self._url_is_file(self.hero_video_url)

    @property
    def promo_video_is_file(self):
        return self._url_is_file(self.promo_video_url)

    social_facebook    = models.CharField(max_length=200, blank=True)
    social_instagram   = models.CharField(max_length=200, blank=True)
    social_tiktok      = models.CharField(max_length=200, blank=True)
    footer_description = models.TextField(default='Faralokun Vital Herbs is a premium herbal wellness brand, blending traditional botanical knowledge with modern quality standards.')
    seo_title          = models.CharField(max_length=200, default='Faralokun Vital Herbs | Premium Herbal Wellness')
    seo_description    = models.TextField(default='Discover premium herbal products and wellness education from Faralokun Vital Herbs — traditional botanical wisdom, modern quality.')
    seo_keywords       = models.TextField(default='herbal wellness, natural remedies, herbal products, wellness education, Lagos')
    about_title        = models.CharField(max_length=200, default='About Faralokun Vital Herbs')
    about_description  = models.TextField(default='A premium herbal wellness brand dedicated to natural healing, education, and quality botanical products.')
    about_mission      = models.TextField(default='To make trusted, high-quality herbal wellness accessible to everyone.')
    about_vision       = models.TextField(default='A world where natural wellness and modern living exist in harmony.')
    registration_no    = models.CharField(max_length=50, default='RC-2705184', blank=True)

    # ── Booking notifications (independent ON/OFF toggles) ─────────────────
    email_notifications_enabled    = models.BooleanField(
        default=True, help_text='Send an email to the address below whenever a new booking comes in.')
    whatsapp_notifications_enabled = models.BooleanField(
        default=False,
        help_text='Send an automatic WhatsApp Business message whenever a new booking comes in. '
                   'Requires WHATSAPP_BUSINESS_API_TOKEN and WHATSAPP_BUSINESS_PHONE_NUMBER_ID to be '
                   'configured on the server -- turning this on without them configured will not '
                   'silently fail; check Notifications in the dashboard or the server logs.')
    booking_notification_email     = models.EmailField(
        blank=True, help_text='Where new-booking emails are sent. Falls back to Contact Email if left blank.')
    booking_whatsapp_number        = models.CharField(
        max_length=20, blank=True,
        help_text='Digits only with country code, e.g. 2348012345678. Receives automatic WhatsApp '
                   'Business booking alerts. Falls back to the WhatsApp Number above if left blank.')

    # ── General notification alerts (inquiries & product orders) ────────────
    notification_email             = models.EmailField(
        blank=True,
        help_text='Where new-inquiry and new-order alerts are sent. Falls back to Contact Email if '
                   'left blank. Booking alerts use Booking Notification Email instead.')
    enquiry_email_notifications_enabled = models.BooleanField(
        default=True,
        help_text='Send an email whenever a new contact/product enquiry comes in.')
    order_email_notifications_enabled   = models.BooleanField(
        default=True,
        help_text='Send an email whenever a new product order comes in.')
    notification_whatsapp_enabled       = models.BooleanField(
        default=False,
        help_text='Send an automatic WhatsApp Business message for new enquiries and orders. '
                    'Requires WHATSAPP_BUSINESS_API_TOKEN and WHATSAPP_BUSINESS_PHONE_NUMBER_ID.')

    # ── Push / sound defaults for the staff dashboard ───────────────────────
    notification_sound_enabled = models.BooleanField(
        default=True,
        help_text='Default sound preference for dashboard notifications. Users can override per '
                   'device in the dashboard.')
    notification_sound = models.CharField(
        max_length=20, default='chime',
        choices=[('chime', 'Chime'), ('gentle', 'Gentle'), ('none', 'Silent')],
        help_text='Default notification sound for the staff dashboard.')

    updated_at         = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Site Settings'
        verbose_name_plural = 'Site Settings'

    def __str__(self):
        return self.site_name

    def save(self, *args, **kwargs):
        # Enforce singleton — only one settings row ever
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @property
    def effective_booking_email(self):
        return self.booking_notification_email or self.contact_email

    @property
    def effective_booking_whatsapp(self):
        return self.booking_whatsapp_number or self.whatsapp_number

    @property
    def effective_notification_email(self):
        return self.notification_email or self.contact_email

    @property
    def effective_notification_whatsapp(self):
        return self.booking_whatsapp_number or self.whatsapp_number


# ── SERVICE ───────────────────────────────────────────────────────────────────
class Service(models.Model):
    CATEGORY_CHOICES = [
        ('herbal_medicine',   'Herbal Medicine'),
        ('spiritual_healing', 'Spiritual Healing'),
        ('cupping',           'Cupping Therapy'),
        ('massage_therapy',   'Massage Therapy'),
        ('dietary_healing',   'Dietary Healing'),
        ('other',             'Other'),
    ]

    title             = models.CharField(max_length=200)
    slug              = models.SlugField(unique=True, blank=True)
    short_description = models.CharField(max_length=300)
    description       = models.TextField()
    image             = CloudinaryField('image', folder='phara/services', blank=True, null=True)
    local_image       = models.CharField(max_length=255, blank=True,
                                         help_text='Absolute static path, e.g. /static/img/health/AhcYq.jpg. No spaces in filenames.')
    icon_name         = models.CharField(max_length=50, default='Leaf',
                                         help_text='Lucide icon name e.g. Leaf, Heart, Star')
    category          = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='other')
    duration_minutes  = models.PositiveIntegerField(default=60)
    price             = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_featured       = models.BooleanField(default=False)
    active            = models.BooleanField(default=True)
    sort_order        = models.PositiveIntegerField(default=0)
    created_at        = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'title']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def image_url(self):
        """Local static path if set, else the Cloudinary URL, else ''."""
        if self.local_image:
            return self.local_image
        try:
            if self.image:
                return self.image.url
        except Exception:
            pass
        return ''


# ── PRODUCT CATEGORY ────────────────────────────────────────────────────────────
class ProductCategory(models.Model):
    name        = models.CharField(max_length=100, unique=True)
    slug        = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    icon_name   = models.CharField(max_length=50, default='Leaf',
                                   help_text='Lucide icon name e.g. Leaf, Flower2, Sprout')
    sort_order  = models.PositiveIntegerField(default=0)
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name_plural = 'Product Categories'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


# ── PRODUCT ───────────────────────────────────────────────────────────────────
class Product(models.Model):
    title             = models.CharField(max_length=200)
    slug              = models.SlugField(unique=True, blank=True)
    category          = models.ForeignKey(ProductCategory, on_delete=models.SET_NULL,
                                          null=True, blank=True, related_name='products')
    short_description = models.CharField(max_length=300)
    description       = models.TextField()
    image             = CloudinaryField('image', folder='phara/products', blank=True, null=True)
    local_image       = models.CharField(
        max_length=300, blank=True,
        help_text='Local file under static/, e.g. /static/img/products/ginger.jpg. '
                  'Shown when no Cloudinary image is set. Survives deployment because '
                  'the file ships inside your codebase.')

    # ── Structured, product-specific information (NOT site settings) ──────────
    ingredients  = models.TextField(blank=True, help_text='One ingredient per line.')
    benefits     = models.TextField(blank=True, help_text='Key benefits/uses, one per line.')
    how_to_use   = models.TextField(blank=True, help_text='Recommended usage / preparation instructions.')
    precautions  = models.TextField(blank=True, help_text='Warnings, contraindications, safety notes.')

    price          = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    track_stock    = models.BooleanField(default=True, help_text='If off, product is always shown as available.')
    stock_quantity = models.PositiveIntegerField(default=0)

    is_featured       = models.BooleanField(default=False)
    active            = models.BooleanField(default=True, help_text='Visible on the public site.')
    sort_order        = models.PositiveIntegerField(default=0)
    created_at        = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'title']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    @property
    def in_stock(self):
        if not self.track_stock:
            return True
        return self.stock_quantity > 0

    def image_url(self):
        """Local static path if set, else the Cloudinary URL, else ''."""
        if self.local_image:
            # Vercel can't serve files whose names contain spaces/dashes, so the
            # files were renamed. Normalize any legacy DB paths to the new names
            # so image_url() never emits a URL that 404s on production.
            legacy = {
                '/static/img/prod/pile- plus.jpeg': '/static/img/prod/pileplus.jpeg',
                '/static/img/prod/pile-plus.jpeg': '/static/img/prod/pileplus.jpeg',
                '/static/img/prod/herbal mixture.jpeg': '/static/img/prod/herbalmixture.jpeg',
                '/static/img/prod/herbal-mixture.jpeg': '/static/img/prod/herbalmixture.jpeg',
            }
            return legacy.get(self.local_image, self.local_image)
        try:
            if self.image:
                return self.image.url
        except Exception:
            pass
        return ''

    @property
    def ingredient_list(self):
        return [i.strip() for i in self.ingredients.splitlines() if i.strip()]

    @property
    def benefit_list(self):
        return [b.strip() for b in self.benefits.splitlines() if b.strip()]

    @property
    def active_promotion(self):
        """
        The single best currently-live promotion for this product, if any.
        Uses the same 'live' definition (is_active + within date range)
        everywhere a promotion is displayed or applied to price.
        """
        now = timezone.now()
        return (self.promotions
                .filter(is_active=True, start_date__lte=now, end_date__gte=now)
                .order_by('-is_featured', 'start_date')
                .first())

    @property
    def has_discount(self):
        return self.active_promotion is not None

    @property
    def display_price(self):
        """Promotional price if a promotion is currently live, else regular price."""
        promo = self.active_promotion
        return promo.promotional_price if promo else self.price

    @property
    def discount_percent(self):
        promo = self.active_promotion
        return promo.discount_percent_display if promo else 0


# ── PRODUCT IMAGE (gallery — additional images beyond the cover photo) ─────────
class ProductImage(models.Model):
    product    = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='gallery_images')
    image      = CloudinaryField('image', folder='phara/products/gallery')
    alt_text   = models.CharField(max_length=200, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self):
        return f'{self.product.title} — image {self.pk}'


# ── PROMOTION ─────────────────────────────────────────────────────────────────
class Promotion(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage Off'),
        ('fixed',      'Fixed Amount Off'),
    ]

    product         = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='promotions')
    discount_type   = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES, default='percentage')
    discount_value  = models.DecimalField(max_digits=10, decimal_places=2,
                                          help_text='Percentage (e.g. 20 for 20%) or a fixed NGN amount, '
                                                     'depending on the type above.')
    start_date      = models.DateTimeField()
    end_date        = models.DateTimeField()
    is_active       = models.BooleanField(default=True, help_text='Turn off to pause without deleting.')
    is_featured     = models.BooleanField(default=False, help_text='Featured promotions are shown first.')
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_featured', 'start_date']

    def __str__(self):
        return f'{self.product.title} — {self.get_discount_type_display()} ({self.discount_value})'

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.start_date and self.end_date and self.end_date <= self.start_date:
            raise ValidationError('End date must be after the start date.')
        if self.discount_type == 'percentage' and self.discount_value and not (0 < self.discount_value <= 100):
            raise ValidationError('Percentage discount must be between 0 and 100.')

    @property
    def is_live(self):
        """True only while active AND within its date window — used everywhere
        a promotion needs to be checked, so expired/paused promotions vanish
        automatically without any manual homepage editing."""
        now = timezone.now()
        return self.is_active and self.start_date <= now <= self.end_date

    @property
    def is_upcoming(self):
        return self.is_active and self.start_date > timezone.now()

    @property
    def is_expired(self):
        return self.end_date < timezone.now()

    @property
    def promotional_price(self):
        price = self.product.price
        if self.discount_type == 'percentage':
            result = price - (price * self.discount_value / 100)
        else:
            result = price - self.discount_value
        return max(result, 0)

    @property
    def discount_percent_display(self):
        """Effective percentage-off, for display, even for fixed-amount promos."""
        if self.discount_type == 'percentage':
            return round(self.discount_value)
        if self.product.price:
            return round((self.discount_value / self.product.price) * 100)
        return 0

    @property
    def savings_amount(self):
        return max(self.product.price - self.promotional_price, 0)

    @classmethod
    def live_qs(cls):
        now = timezone.now()
        return (cls.objects
                .filter(is_active=True, start_date__lte=now, end_date__gte=now, product__active=True)
                .select_related('product', 'product__category')
                .order_by('-is_featured', 'start_date'))


# ── CART (session-based; guest checkout, no account required) ──────────────────
class Cart(models.Model):
    session_key = models.CharField(max_length=40, unique=True, db_index=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Cart {self.session_key[:8]}'

    @property
    def item_list(self):
        return self.cart_items.select_related('product', 'product__category').order_by('id')

    @property
    def total_items(self):
        return sum(i.quantity for i in self.item_list)

    @property
    def subtotal(self):
        return sum(i.line_total for i in self.item_list)


class CartItem(models.Model):
    cart       = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='cart_items')
    product    = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='cart_items')
    quantity   = models.PositiveIntegerField(default=1)
    added_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cart', 'product')

    def __str__(self):
        return f'{self.quantity}x {self.product.title}'

    @property
    def unit_price(self):
        return self.product.display_price

    @property
    def line_total(self):
        return self.unit_price * self.quantity


# ── ORDER (multi-item checkout — no online payment; staff follow up) ───────────
class Order(models.Model):
    STATUS_CHOICES = [
        ('pending',    'Pending'),
        ('confirmed',  'Confirmed'),
        ('processing', 'Processing'),
        ('ready',      'Ready'),
        ('completed',  'Completed'),
        ('cancelled',  'Cancelled'),
    ]

    order_number     = models.CharField(max_length=20, unique=True, editable=False)
    customer_name    = models.CharField(max_length=200)
    customer_phone   = models.CharField(max_length=20)
    customer_email   = models.EmailField(blank=True)
    delivery_address = models.TextField(blank=True)
    notes            = models.TextField(blank=True)
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    subtotal         = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Order {self.order_number} — {self.customer_name}'

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self._generate_order_number()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_order_number():
        import random, string
        while True:
            candidate = 'GHC' + timezone.now().strftime('%y%m%d') + ''.join(
                random.choices(string.digits, k=4))
            if not Order.objects.filter(order_number=candidate).exists():
                return candidate

    @property
    def total(self):
        return self.subtotal

    @property
    def item_count(self):
        return sum(i.quantity for i in self.items.all())


class OrderItem(models.Model):
    order        = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product      = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, related_name='order_items')
    product_name = models.CharField(max_length=200)   # snapshot in case product changes/is removed
    unit_price   = models.DecimalField(max_digits=10, decimal_places=2)  # snapshot at time of order
    quantity     = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f'{self.quantity}x {self.product_name}'

    @property
    def line_total(self):
        return self.unit_price * self.quantity


# ── APPOINTMENT ───────────────────────────────────────────────────────────────
class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending',   'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]

    TIME_CHOICES = [(f'{h:02d}:{m:02d}', f'{h:02d}:{m:02d}')
                    for h in range(8, 19) for m in (0, 30)]

    # Nullable so guest bookings (no account) keep working unchanged.
    # Registered patients get an explicit link instead of relying on
    # contact_email == user.email, which breaks if either changes.
    patient           = models.ForeignKey('accounts.PatientProfile', on_delete=models.SET_NULL,
                                          null=True, blank=True, related_name='linked_appointments')
    service           = models.ForeignKey(Service, on_delete=models.SET_NULL,
                                         null=True, blank=True, related_name='appointments')
    service_name      = models.CharField(max_length=200, blank=True)   # snapshot
    appointment_date  = models.DateField(null=True, blank=True)
    preferred_time    = models.CharField(max_length=10, choices=TIME_CHOICES, blank=True)
    status            = models.CharField(max_length=20, choices=STATUS_CHOICES,
                                        default='pending', db_index=True)
    contact_name      = models.CharField(max_length=200)
    contact_email     = models.EmailField(blank=True)
    contact_phone     = models.CharField(max_length=20)
    notes             = models.TextField(blank=True)
    created_at        = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['appointment_date', 'preferred_time'],
                condition=models.Q(status='confirmed'),
                name='unique_confirmed_slot',
            ),
        ]

    def __str__(self):
        return f'{self.contact_name} — {self.service_name or "General"} ({self.status})'

    def save(self, *args, **kwargs):
        if self.service and not self.service_name:
            self.service_name = self.service.title
        super().save(*args, **kwargs)

    def conflicts_with_confirmed(self):
        """
        True if another appointment already holds the CONFIRMED slot at this
        exact date+time. There's no practitioner roster anymore -- the
        business handles one confirmed consultation per slot -- so this is
        a straightforward date+time collision check, used by staff
        confirmation (dashboard.views.appointment_update_status).
        """
        if not (self.appointment_date and self.preferred_time):
            return False
        qs = Appointment.objects.filter(
            status='confirmed',
            appointment_date=self.appointment_date,
            preferred_time=self.preferred_time,
        )
        if self.pk:
            qs = qs.exclude(pk=self.pk)
        return qs.exists()

    @classmethod
    def slot_is_available(cls, appointment_date, preferred_time):
        """
        Used by the public booking form (api.forms.AppointmentForm.clean) to
        reject requests for a date+time that's already CONFIRMED for someone
        else. Two PENDING requests for the same slot are fine -- staff
        resolves which one is actually confirmed.
        """
        if not (appointment_date and preferred_time):
            return True
        return not cls.objects.filter(
            status='confirmed', appointment_date=appointment_date, preferred_time=preferred_time
        ).exists()


# ── BLOG POST ─────────────────────────────────────────────────────────────────
class BlogPost(models.Model):
    title        = models.CharField(max_length=300)
    slug         = models.SlugField(unique=True, blank=True)
    excerpt      = models.CharField(max_length=400)
    content      = models.TextField()
    image        = CloudinaryField('image', folder='phara/blog', blank=True, null=True)
    local_image = models.CharField(max_length=255, blank=True,
                                   help_text='Absolute static path, e.g. /static/img/health/qLDdj.jpg. No spaces in filenames.')
    category     = models.CharField(max_length=100, blank=True)
    author       = models.CharField(max_length=100, default='Faralokun Vital Herbs Team')
    is_published = models.BooleanField(default=False, db_index=True)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-published_at', '-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        from django.utils import timezone
        if self.is_published and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    @property
    def reading_time(self):
        word_count = len(self.content.split())
        return max(1, round(word_count / 200))

    def image_url(self):
        """Local static path if set, else the Cloudinary URL, else ''."""
        if self.local_image:
            return self.local_image
        try:
            if self.image:
                return self.image.url
        except Exception:
            pass
        return ''


# ── INQUIRY ───────────────────────────────────────────────────────────────────
class Inquiry(models.Model):
    name       = models.CharField(max_length=200)
    email      = models.EmailField(blank=True)
    phone      = models.CharField(max_length=20, blank=True)
    message    = models.TextField()
    is_read    = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Inquiries'

    def __str__(self):
        return f'Inquiry from {self.name}'


# ── TESTIMONIAL ───────────────────────────────────────────────────────────────
class Testimonial(models.Model):
    name        = models.CharField(max_length=200)
    location    = models.CharField(max_length=100, blank=True)
    content     = models.TextField()
    condition   = models.CharField(max_length=100, blank=True,
                                   help_text='e.g. Fibroid Treatment, Diabetes')
    rating      = models.PositiveSmallIntegerField(default=5)
    is_approved = models.BooleanField(default=False, db_index=True)
    sort_order  = models.PositiveIntegerField(default=0)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order', '-created_at']

    def __str__(self):
        return f'{self.name} — {self.condition or "General"}'


# ── SUBSCRIBER ────────────────────────────────────────────────────────────────
class Subscriber(models.Model):
    email         = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email


# ── NOTIFICATION ──────────────────────────────────────────────────────────────
class Notification(models.Model):
    TYPE_CHOICES = [
        ('appointment',    'New Appointment'),
        ('inquiry',        'New Inquiry'),
        ('order',          'New Order'),
        ('subscriber',     'New Subscriber'),
        ('promotion',      'Promotion Alert'),
        ('general',        'General'),
    ]

    type       = models.CharField(max_length=30, choices=TYPE_CHOICES, default='general')
    title      = models.CharField(max_length=200)
    message    = models.TextField()
    url        = models.CharField(max_length=500, blank=True,
                                  help_text='Dashboard link to the related record, e.g. /dashboard/orders/12/')
    is_read    = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


# ── PUSH SUBSCRIPTION (Web Push / VAPID device registration) ─────────────────
# One row per browser/device a staff member has enabled notifications on.
# Subscriptions are tied to a user so push can be revoked/removed per device.
# The endpoint/key material is required by the Web Push protocol to deliver
# messages; VAPID private keys never leave the server (settings).
class PushSubscription(models.Model):
    user     = models.ForeignKey('auth.User', on_delete=models.CASCADE,
                                 related_name='push_subscriptions')
    endpoint = models.CharField(max_length=500, unique=True, db_index=True)
    p256dh   = models.CharField(max_length=255, help_text='Public key (base64url) from PushSubscription.getKey("p256dh").')
    auth     = models.CharField(max_length=255, help_text='Authentication secret (base64url) from PushSubscription.getKey("auth").')
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        ordering = ['-last_used_at']

    def __str__(self):
        return f"Push device for {self.user.username} ({self.endpoint[:60]}…)"
