from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display, action
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
import logging
from .models import (
    SiteSettings, Service, Product, ProductCategory, ProductImage, Promotion,
    Order, OrderItem,
    Appointment, BlogPost, Inquiry,
    Testimonial, Subscriber, Notification
)

logger = logging.getLogger(__name__)

# ── SITE SETTINGS ─────────────────────────────────────────────────────────────
@admin.register(SiteSettings)
class SiteSettingsAdmin(ModelAdmin):
    fieldsets = (
        ('Branding', {
            'fields': ('site_name', 'tagline', 'logo', 'logo_contains_name', 'favicon',
                       'primary_color', 'secondary_color', 'accent_color', 'registration_no')
        }),
        ('Contact', {
            'fields': ('contact_email', 'contact_phone', 'contact_phone2',
                       'whatsapp_number', 'whatsapp_greeting', 'address', 'city', 'country')
        }),
        ('Hero Section', {
            'fields': ('hero_headline', 'hero_subheadline',
                       'hero_cta_primary', 'hero_cta_secondary', 'hero_video_url')
        }),
        ('About', {
            'fields': ('about_title', 'about_description', 'about_mission', 'about_vision')
        }),
        ('Social & Footer', {
            'fields': ('social_facebook', 'social_instagram', 'social_tiktok', 'footer_description')
        }),
        ('SEO', {
            'fields': ('seo_title', 'seo_description', 'seo_keywords')
        }),
    )

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


# ── SERVICES ──────────────────────────────────────────────────────────────────
@admin.register(Service)
class ServiceAdmin(ModelAdmin):
    list_display        = ['title', 'category_badge', 'duration_minutes',
                           'price_display', 'featured_icon', 'status_toggle', 'sort_order', 'actions_col']
    list_filter         = ['category', 'is_featured', 'active']
    list_editable       = ['sort_order']
    search_fields       = ['title', 'description', 'short_description']
    prepopulated_fields = {'slug': ('title',)}
    ordering            = ['sort_order', 'title']
    actions             = ['make_active', 'make_inactive', 'make_featured', 'remove_featured']

    fieldsets = (
        ('Basic Info',        {'fields': ('title', 'slug', 'category', 'icon_name', 'sort_order')}),
        ('Content',           {'fields': ('short_description', 'description', 'image', 'local_image')}),
        ('Pricing & Duration',{'fields': ('price', 'duration_minutes')}),
        ('Visibility',        {'fields': ('active', 'is_featured')}),
    )

    @admin.display(description='Category')
    def category_badge(self, obj):
        colors = {
            'herbal_medicine':   '#3A7D44',
            'spiritual_healing': '#C49A3C',
            'cupping':           '#4CAF50',
            'massage_therapy':   '#B0683A',
            'dietary_healing':   '#A0B5A3',
            'other':             '#666',
        }
        color = colors.get(obj.category, '#666')
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:12px;font-size:11px;">{}</span>',
            color, obj.get_category_display()
        )

    @admin.display(description='Price')
    def price_display(self, obj):
        if obj.price > 0:
            price = '{:,.0f}'.format(obj.price)
            return format_html('<strong>NGN {}</strong>', price)
        return format_html('<span style="color:#999;">Free</span>')

    @admin.display(description='Featured')
    def featured_icon(self, obj):
        if obj.is_featured:
            return format_html('<span style="color:#C49A3C;font-size:16px;">&#9733;</span>')
        return format_html('<span style="color:#ccc;font-size:16px;">&#9734;</span>')

    @admin.display(description='Status')
    def status_toggle(self, obj):
        if obj.active:
            return format_html(
                '<span style="background:#3A7D44;color:white;padding:2px 10px;border-radius:12px;font-size:11px;">Active</span>'
            )
        return format_html(
            '<span style="background:#888;color:white;padding:2px 10px;border-radius:12px;font-size:11px;">Hidden</span>'
        )

    @admin.display(description='Actions')
    def actions_col(self, obj):
        edit_url = reverse('admin:api_service_change', args=[obj.pk])
        del_url  = reverse('admin:api_service_delete', args=[obj.pk])
        return format_html(
            '<a href="{}" style="color:#3A7D44;margin-right:8px;">Edit</a>'
            '<a href="{}" style="color:#e53e3e;" onclick="return confirm(\'Delete this service?\')">Delete</a>',
            edit_url, del_url
        )

    @admin.action(description='Mark selected as Active (visible on site)')
    def make_active(self, request, queryset):
        updated = queryset.update(active=True)
        self.message_user(request, f'{updated} service(s) marked as Active.')

    @admin.action(description='Mark selected as Inactive (hidden from site)')
    def make_inactive(self, request, queryset):
        updated = queryset.update(active=False)
        self.message_user(request, f'{updated} service(s) marked as Inactive.')

    @admin.action(description='Mark selected as Featured')
    def make_featured(self, request, queryset):
        queryset.update(is_featured=True)
        self.message_user(request, 'Services marked as featured.')

    @admin.action(description='Remove Featured status')
    def remove_featured(self, request, queryset):
        queryset.update(is_featured=False)
        self.message_user(request, 'Featured status removed.')


# ── PRODUCT CATEGORIES ────────────────────────────────────────────────────────
@admin.register(ProductCategory)
class ProductCategoryAdmin(ModelAdmin):
    list_display        = ['name', 'sort_order', 'is_active']
    list_editable        = ['sort_order', 'is_active']
    search_fields        = ['name']
    prepopulated_fields  = {'slug': ('name',)}
    ordering             = ['sort_order', 'name']


class ProductImageInline(TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'alt_text', 'sort_order']


# ── PRODUCTS ──────────────────────────────────────────────────────────────────
@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display        = ['title', 'category', 'price_display', 'promo_badge', 'stock_badge',
                           'featured_icon', 'status_badge', 'sort_order', 'action_links']
    list_filter         = ['category', 'is_featured', 'active', 'track_stock']
    list_editable       = ['sort_order']
    search_fields       = ['title', 'description', 'short_description']
    prepopulated_fields = {'slug': ('title',)}
    ordering            = ['sort_order', 'title']
    actions             = ['make_active', 'make_inactive', 'make_featured', 'remove_featured']
    inlines             = [ProductImageInline]

    fieldsets = (
        ('Basic Info', {'fields': ('title', 'slug', 'category', 'sort_order')}),
        ('Content',    {'fields': ('short_description', 'description', 'image', 'local_image')}),
        ('Product Details', {'fields': ('ingredients', 'benefits', 'how_to_use', 'precautions')}),
        ('Pricing & Stock', {'fields': ('price', 'track_stock', 'stock_quantity')}),
        ('Visibility', {'fields': ('active', 'is_featured')}),
    )

    @admin.display(description='Price')
    def price_display(self, obj):
        price = '{:,.0f}'.format(obj.price)
        return format_html('<strong>NGN {}</strong>', price)

    @admin.display(description='Promotion')
    def promo_badge(self, obj):
        promo = obj.active_promotion
        if promo:
            return format_html(
                '<span style="background:#B0683A;color:white;padding:2px 10px;border-radius:12px;font-size:11px;">-{}%</span>',
                promo.discount_percent_display
            )
        return '—'

    @admin.display(description='Stock')
    def stock_badge(self, obj):
        if not obj.track_stock:
            return format_html('<span style="color:#5f7768;">Not tracked</span>')
        if obj.stock_quantity <= 0:
            return format_html('<span style="background:#e53e3e;color:white;padding:2px 10px;border-radius:12px;font-size:11px;">Out of stock</span>')
        if obj.stock_quantity <= 5:
            return format_html('<span style="background:#C49A3C;color:white;padding:2px 10px;border-radius:12px;font-size:11px;">Low: {}</span>', obj.stock_quantity)
        return str(obj.stock_quantity)

    @admin.display(description='Featured')
    def featured_icon(self, obj):
        if obj.is_featured:
            return format_html('<span style="color:#C49A3C;">&#9733; Featured</span>')
        return '—'

    @admin.display(description='Status')
    def status_badge(self, obj):
        if obj.active:
            return format_html(
                '<span style="background:#3A7D44;color:white;padding:2px 10px;border-radius:12px;font-size:11px;">Available</span>'
            )
        return format_html(
            '<span style="background:#e53e3e;color:white;padding:2px 10px;border-radius:12px;font-size:11px;">Unavailable</span>'
        )

    @admin.display(description='Actions')
    def action_links(self, obj):
        edit_url = reverse('admin:api_product_change', args=[obj.pk])
        del_url  = reverse('admin:api_product_delete', args=[obj.pk])
        return format_html(
            '<a href="{}" style="color:#3A7D44;margin-right:8px;">Edit</a>'
            '<a href="{}" style="color:#e53e3e;" onclick="return confirm(\'Delete this product?\')">Delete</a>',
            edit_url, del_url
        )

    @admin.action(description='Mark selected as Available (show on site)')
    def make_active(self, request, queryset):
        updated = queryset.update(active=True)
        self.message_user(request, f'{updated} product(s) marked as Available.')

    @admin.action(description='Mark as Unavailable (hide from site, keep record)')
    def make_inactive(self, request, queryset):
        updated = queryset.update(active=False)
        self.message_user(request, f'{updated} product(s) marked as Unavailable.')

    @admin.action(description='Mark selected as Featured')
    def make_featured(self, request, queryset):
        queryset.update(is_featured=True)
        self.message_user(request, 'Products marked as featured.')

    @admin.action(description='Remove Featured status')
    def remove_featured(self, request, queryset):
        queryset.update(is_featured=False)
        self.message_user(request, 'Featured status removed.')


# ── PROMOTIONS ────────────────────────────────────────────────────────────────
@admin.register(Promotion)
class PromotionAdmin(ModelAdmin):
    list_display  = ['product', 'discount_type', 'discount_value', 'start_date', 'end_date',
                     'live_badge', 'is_featured']
    list_filter   = ['discount_type', 'is_active', 'is_featured']
    search_fields = ['product__title']
    ordering      = ['-is_featured', 'start_date']
    autocomplete_fields = []

    fieldsets = (
        ('Promotion', {'fields': ('product', 'discount_type', 'discount_value')}),
        ('Schedule',  {'fields': ('start_date', 'end_date')}),
        ('Visibility', {'fields': ('is_active', 'is_featured')}),
    )

    @admin.display(description='Status')
    def live_badge(self, obj):
        if obj.is_live:
            return format_html('<span style="background:#3A7D44;color:white;padding:2px 10px;border-radius:12px;font-size:11px;">Live</span>')
        if obj.is_upcoming:
            return format_html('<span style="background:#C49A3C;color:white;padding:2px 10px;border-radius:12px;font-size:11px;">Upcoming</span>')
        if obj.is_expired:
            return format_html('<span style="background:#5f7768;color:white;padding:2px 10px;border-radius:12px;font-size:11px;">Expired</span>')
        return format_html('<span style="background:#e53e3e;color:white;padding:2px 10px;border-radius:12px;font-size:11px;">Paused</span>')


# ── ORDERS ─────────────────────────────────────────────────────────────────────
class OrderItemInline(TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'product_name', 'unit_price', 'quantity']
    can_delete = False


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display    = ['order_number', 'customer_name', 'customer_phone',
                       'item_count', 'total_display', 'status_badge', 'created_at', 'action_links']
    list_filter     = ['status', 'created_at']
    search_fields   = ['order_number', 'customer_name', 'customer_phone', 'customer_email']
    readonly_fields = ['order_number', 'subtotal', 'created_at', 'updated_at']
    ordering        = ['-created_at']
    actions         = ['mark_confirmed', 'mark_completed', 'mark_cancelled']
    inlines         = [OrderItemInline]

    fieldsets = (
        ('Order Info',  {'fields': ('order_number', 'subtotal')}),
        ('Customer',    {'fields': ('customer_name', 'customer_phone', 'customer_email', 'delivery_address', 'notes')}),
        ('Status',      {'fields': ('status',)}),
        ('Timestamps',  {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    @admin.display(description='Total')
    def total_display(self, obj):
        total = '{:,.0f}'.format(obj.total)
        return format_html('<strong>NGN {}</strong>', total)

    @admin.display(description='Status')
    def status_badge(self, obj):
        colors = {
            'pending':    ('#856404', '#fff3cd'),
            'confirmed':  ('#155724', '#d4edda'),
            'processing': ('#0c4a6e', '#dbeafe'),
            'ready':      ('#3730a3', '#e0e7ff'),
            'completed':  ('#0c3a1f', '#c3e6cb'),
            'cancelled':  ('#721c24', '#f8d7da'),
        }
        color, bg = colors.get(obj.status, ('#333', '#eee'))
        label = obj.get_status_display()
        return format_html(
            '<span style="background:{};color:{};padding:2px 10px;border-radius:12px;font-size:11px;">{}</span>',
            bg, color, label
        )

    @admin.display(description='Actions')
    def action_links(self, obj):
        edit_url = reverse('admin:api_order_change', args=[obj.pk])
        del_url  = reverse('admin:api_order_delete', args=[obj.pk])
        return format_html(
            '<a href="{}" style="color:#3A7D44;margin-right:8px;">View</a>'
            '<a href="{}" style="color:#e53e3e;" onclick="return confirm(\'Delete this order?\')">Delete</a>',
            edit_url, del_url
        )

    @admin.action(description='Mark as Confirmed')
    def mark_confirmed(self, request, queryset):
        queryset.update(status='confirmed')
        self.message_user(request, 'Orders marked as Confirmed.')

    @admin.action(description='Mark as Completed')
    def mark_completed(self, request, queryset):
        queryset.update(status='completed', updated_at=timezone.now())
        self.message_user(request, 'Orders marked as Completed.')

    @admin.action(description='Mark as Cancelled')
    def mark_cancelled(self, request, queryset):
        queryset.update(status='cancelled')
        self.message_user(request, 'Orders cancelled.')


# ── APPOINTMENTS ──────────────────────────────────────────────────────────────
@admin.register(Appointment)
class AppointmentAdmin(ModelAdmin):
    list_display    = ['contact_name', 'contact_phone', 'service_name',
                       'date_time_display', 'status_badge', 'created_at', 'action_links']
    list_filter     = ['status', 'appointment_date', 'created_at']
    search_fields   = ['contact_name', 'contact_phone', 'contact_email', 'service_name', 'notes']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy  = 'created_at'
    ordering        = ['-created_at']
    actions         = ['confirm_appointments', 'complete_appointments', 'cancel_appointments']

    fieldsets = (
        ('Patient',     {'fields': ('contact_name', 'contact_phone', 'contact_email')}),
        ('Appointment', {'fields': ('service', 'service_name', 'appointment_date', 'preferred_time', 'notes')}),
        ('Status',      {'fields': ('status',)}),
        ('Timestamps',  {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    @admin.display(description='Date & Time')
    def date_time_display(self, obj):
        date = str(obj.appointment_date) if obj.appointment_date else 'TBC'
        time = obj.preferred_time or ''
        return format_html(
            '<strong>{}</strong><br/><small style="color:#999;">{}</small>',
            date, time
        )

    @admin.display(description='Status')
    def status_badge(self, obj):
        configs = {
            'pending':   ('#856404', '#fff3cd'),
            'confirmed': ('#155724', '#d4edda'),
            'completed': ('#0c3a1f', '#c3e6cb'),
            'cancelled': ('#721c24', '#f8d7da'),
        }
        color, bg = configs.get(obj.status, ('#333', '#eee'))
        label = obj.get_status_display()
        return format_html(
            '<span style="background:{};color:{};padding:3px 10px;border-radius:12px;font-size:11px;">{}</span>',
            bg, color, label
        )

    @admin.display(description='Actions')
    def action_links(self, obj):
        edit_url = reverse('admin:api_appointment_change', args=[obj.pk])
        del_url  = reverse('admin:api_appointment_delete', args=[obj.pk])
        pdf_url  = reverse('api:admin_receipt_pdf', args=[obj.pk])
        return format_html(
            '<a href="{}" style="color:#3A7D44;margin-right:6px;">Edit</a>'
            '<a href="{}" style="color:#3A7D44;margin-right:6px;" target="_blank">PDF</a>'
            '<a href="{}" style="color:#e53e3e;" onclick="return confirm(\'Delete this appointment?\')">Delete</a>',
            edit_url, pdf_url, del_url
        )

    @admin.action(description='Confirm selected appointments')
    def confirm_appointments(self, request, queryset):
        # Capture which appointments are actually about to change before updating,
        # so we only email the ones we just confirmed — not every already-confirmed
        # appointment that happened to be part of the admin's selection.
        to_confirm_ids = list(queryset.filter(status='pending').values_list('pk', flat=True))
        updated = queryset.filter(pk__in=to_confirm_ids).update(status='confirmed')
        from .email_service import send_appointment_status_update
        for appt in queryset.filter(pk__in=to_confirm_ids):
            try:
                send_appointment_status_update(appt)
            except Exception:
                logger.exception(f'Failed to send status-update email for appointment {appt.pk}')
        self.message_user(request, f'{updated} appointment(s) confirmed.')

    @admin.action(description='Mark selected as Completed')
    def complete_appointments(self, request, queryset):
        to_complete_ids = list(queryset.exclude(status='completed').values_list('pk', flat=True))
        updated = queryset.filter(pk__in=to_complete_ids).update(status='completed')
        from .email_service import send_appointment_status_update
        for appt in queryset.filter(pk__in=to_complete_ids):
            try:
                send_appointment_status_update(appt)
            except Exception:
                logger.exception(f'Failed to send status-update email for appointment {appt.pk}')
        self.message_user(request, f'{updated} appointment(s) marked as completed.')

    @admin.action(description='Cancel selected appointments')
    def cancel_appointments(self, request, queryset):
        to_cancel_ids = list(queryset.exclude(status='cancelled').values_list('pk', flat=True))
        updated = queryset.filter(pk__in=to_cancel_ids).update(status='cancelled')
        from .email_service import send_appointment_status_update
        for appt in queryset.filter(pk__in=to_cancel_ids):
            try:
                send_appointment_status_update(appt)
            except Exception:
                logger.exception(f'Failed to send status-update email for appointment {appt.pk}')
        self.message_user(request, f'{updated} appointment(s) cancelled.')


# ── BLOG POSTS ────────────────────────────────────────────────────────────────
@admin.register(BlogPost)
class BlogPostAdmin(ModelAdmin):
    list_display        = ['title', 'author', 'category', 'reading_time_display',
                           'published_badge', 'published_at', 'action_links']
    list_filter         = ['is_published', 'category', 'created_at']
    search_fields       = ['title', 'content', 'author', 'excerpt']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields     = ['created_at', 'updated_at']
    ordering            = ['-created_at']
    actions             = ['publish_posts', 'unpublish_posts']

    fieldsets = (
        ('Content',    {'fields': ('title', 'slug', 'excerpt', 'content', 'image', 'local_image')}),
        ('Meta',       {'fields': ('author', 'category')}),
        ('Publishing', {'fields': ('is_published', 'published_at')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    @admin.display(description='Read Time')
    def reading_time_display(self, obj):
        return f'{obj.reading_time} min read'

    @admin.display(description='Status')
    def published_badge(self, obj):
        if obj.is_published:
            return format_html(
                '<span style="background:#3A7D44;color:white;padding:2px 10px;border-radius:12px;font-size:11px;">Published</span>'
            )
        return format_html(
            '<span style="background:#888;color:white;padding:2px 10px;border-radius:12px;font-size:11px;">Draft</span>'
        )

    @admin.display(description='Actions')
    def action_links(self, obj):
        edit_url = reverse('admin:api_blogpost_change', args=[obj.pk])
        del_url  = reverse('admin:api_blogpost_delete', args=[obj.pk])
        return format_html(
            '<a href="{}" style="color:#3A7D44;margin-right:8px;">Edit</a>'
            '<a href="{}" style="color:#e53e3e;" onclick="return confirm(\'Delete this post?\')">Delete</a>',
            edit_url, del_url
        )

    @admin.action(description='Publish selected posts')
    def publish_posts(self, request, queryset):
        updated = queryset.update(is_published=True, published_at=timezone.now())
        self.message_user(request, f'{updated} post(s) published.')

    @admin.action(description='Unpublish (revert to Draft)')
    def unpublish_posts(self, request, queryset):
        updated = queryset.update(is_published=False)
        self.message_user(request, f'{updated} post(s) moved to Draft.')


# ── INQUIRIES ─────────────────────────────────────────────────────────────────
@admin.register(Inquiry)
class InquiryAdmin(ModelAdmin):
    list_display    = ['name', 'email_link', 'phone_link', 'message_preview',
                       'read_badge', 'created_at', 'action_links']
    list_filter     = ['is_read', 'created_at']
    search_fields   = ['name', 'email', 'phone', 'message']
    readonly_fields = ['name', 'email', 'phone', 'message', 'created_at']
    ordering        = ['-created_at']
    actions         = ['mark_read', 'mark_unread']

    @admin.display(description='Email')
    def email_link(self, obj):
        if obj.email:
            return format_html(
                '<a href="mailto:{}" style="color:#3A7D44;">{}</a>', obj.email, obj.email
            )
        return '—'

    @admin.display(description='Phone')
    def phone_link(self, obj):
        if obj.phone:
            return format_html(
                '<a href="tel:{}" style="color:#3A7D44;">{}</a>', obj.phone, obj.phone
            )
        return '—'

    @admin.display(description='Message')
    def message_preview(self, obj):
        return obj.message[:60] + '…' if len(obj.message) > 60 else obj.message

    @admin.display(description='Status')
    def read_badge(self, obj):
        if obj.is_read:
            return format_html(
                '<span style="background:#888;color:white;padding:2px 8px;border-radius:12px;font-size:11px;">Read</span>'
            )
        return format_html(
            '<span style="background:#C49A3C;color:white;padding:2px 8px;border-radius:12px;font-size:11px;">New</span>'
        )

    @admin.display(description='Actions')
    def action_links(self, obj):
        edit_url = reverse('admin:api_inquiry_change', args=[obj.pk])
        del_url  = reverse('admin:api_inquiry_delete', args=[obj.pk])
        return format_html(
            '<a href="{}" style="color:#3A7D44;margin-right:8px;">View</a>'
            '<a href="{}" style="color:#e53e3e;" onclick="return confirm(\'Delete this inquiry?\')">Delete</a>',
            edit_url, del_url
        )

    @admin.action(description='Mark selected as Read')
    def mark_read(self, request, queryset):
        queryset.update(is_read=True)
        self.message_user(request, 'Inquiries marked as read.')

    @admin.action(description='Mark selected as Unread')
    def mark_unread(self, request, queryset):
        queryset.update(is_read=False)
        self.message_user(request, 'Inquiries marked as unread.')


# ── TESTIMONIALS ──────────────────────────────────────────────────────────────
@admin.register(Testimonial)
class TestimonialAdmin(ModelAdmin):
    list_display    = ['name', 'location', 'condition', 'stars_display',
                       'approved_badge', 'sort_order', 'action_links']
    list_filter     = ['is_approved', 'rating']
    list_editable   = ['sort_order']
    search_fields   = ['name', 'content', 'condition', 'location']
    ordering        = ['sort_order', '-created_at']
    actions         = ['approve', 'unapprove']

    @admin.display(description='Rating')
    def stars_display(self, obj):
        filled = '★' * obj.rating
        empty  = '★' * (5 - obj.rating)
        return format_html(
            '<span style="color:#C49A3C;">{}</span><span style="color:#ddd;">{}</span>',
            filled, empty
        )

    @admin.display(description='Status')
    def approved_badge(self, obj):
        if obj.is_approved:
            return format_html(
                '<span style="background:#3A7D44;color:white;padding:2px 10px;border-radius:12px;font-size:11px;">Approved</span>'
            )
        return format_html(
            '<span style="background:#C49A3C;color:white;padding:2px 10px;border-radius:12px;font-size:11px;">Pending</span>'
        )

    @admin.display(description='Actions')
    def action_links(self, obj):
        edit_url = reverse('admin:api_testimonial_change', args=[obj.pk])
        del_url  = reverse('admin:api_testimonial_delete', args=[obj.pk])
        return format_html(
            '<a href="{}" style="color:#3A7D44;margin-right:8px;">Edit</a>'
            '<a href="{}" style="color:#e53e3e;" onclick="return confirm(\'Delete this testimonial?\')">Delete</a>',
            edit_url, del_url
        )

    @admin.action(description='Approve selected (show on site)')
    def approve(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} testimonial(s) approved.')

    @admin.action(description='Unapprove (hide from site)')
    def unapprove(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'{updated} testimonial(s) hidden.')


# ── SUBSCRIBERS ───────────────────────────────────────────────────────────────
@admin.register(Subscriber)
class SubscriberAdmin(ModelAdmin):
    list_display    = ['email', 'subscribed_at', 'action_links']
    search_fields   = ['email']
    readonly_fields = ['subscribed_at']
    ordering        = ['-subscribed_at']

    @admin.display(description='Actions')
    def action_links(self, obj):
        del_url = reverse('admin:api_subscriber_delete', args=[obj.pk])
        return format_html(
            '<a href="{}" style="color:#e53e3e;" onclick="return confirm(\'Remove this subscriber?\')">Remove</a>',
            del_url
        )


# ── NOTIFICATIONS ─────────────────────────────────────────────────────────────
@admin.register(Notification)
class NotificationAdmin(ModelAdmin):
    list_display    = ['title', 'type_badge', 'read_badge', 'created_at']
    list_filter     = ['type', 'is_read', 'created_at']
    search_fields   = ['title', 'message']
    readonly_fields = ['created_at']
    ordering        = ['-created_at']
    actions         = ['mark_all_read']

    @admin.display(description='Type')
    def type_badge(self, obj):
        colors = {
            'appointment':   '#3A7D44',
            'inquiry':       '#C49A3C',
            'order': '#B0683A',
            'promotion': '#C49A3C',
            'subscriber':    '#A0B5A3',
            'general':       '#666',
        }
        color = colors.get(obj.type, '#666')
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:12px;font-size:11px;">{}</span>',
            color, obj.get_type_display()
        )

    @admin.display(description='Status')
    def read_badge(self, obj):
        if obj.is_read:
            return format_html('<span style="color:#999;font-size:11px;">Read</span>')
        return format_html(
            '<span style="background:#C49A3C;color:white;padding:2px 8px;border-radius:12px;font-size:11px;">New</span>'
        )

    @admin.action(description='Mark all selected as Read')
    def mark_all_read(self, request, queryset):
        queryset.update(is_read=True)
        self.message_user(request, 'Notifications marked as read.')