from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.db import transaction
import json
import logging

logger = logging.getLogger(__name__)

from .models import (
    SiteSettings, Service, Product, ProductCategory, Promotion,
    Appointment, BlogPost, Inquiry, Testimonial, Subscriber, Notification,
    Cart, CartItem, Order, OrderItem,
)
from .forms import (
    AppointmentForm, InquiryForm, AddToCartForm, CheckoutForm,
    SubscriberForm, TestimonialForm, ProductEnquiryForm
)
from .utils import (
    create_notification, trigger_whatsapp_alert, notify_new_booking,
    build_appointment_wa_message, build_order_wa_message, build_inquiry_wa_message,
    notify_new_inquiry, notify_new_product_enquiry, notify_new_order,
    build_cart_whatsapp_url,
)
from .cart import get_cart
from .email_service import send_appointment_confirmation

TRUST_INDICATORS = [
    ('Expert Herbal Guidance', 'Qualified & Trusted'),
    ('Traditional & Herbal Care', '100% Natural Remedies'),
    ('Personalized Attention', 'Care Just for You'),
    ('Confidential Service', 'Private & Secure'),
]

CONDITIONS = [
    'Spiritual Divination','Financial Problems','Barrenness','Business Promotion',
    'Long Lasting Marriage','Marriage Compatibility','Stomach Ulcer','Diabetes',
    'Low Sperm Count','Tuberculosis','Strokes','Typhoid Fever','Rheumatism',
    'Fibroid','Gonorrhea','Menstruation Malfunction','Piles','Asthma',
    'Man-power','Virginal Discharge','Hypertension','Malaria','Family Planning',
    'Toilet Infections','Anaemia','Menstruation Pain','Pelvic Inflammatory','Blood Disease',
]

VALUES = [
    ('Compassion','Every patient deserves empathy, dignity, and respect on their healing journey.','M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z'),
    ('Integrity','We uphold the highest standards of traditional medicine ethics and patient care.','M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z'),
    ('Wholeness','True healing addresses body, mind, and spirit in complete harmony.','M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064'),
]
HOURS = [
    ('Monday – Friday','8:00 AM – 6:00 PM'),
    ('Saturday','9:00 AM – 4:00 PM'),
    ('Sunday','By Appointment'),
]


def home(request):
    explore_links = [
        ('Our Services', reverse('api:services'), 'M12 2v20M2 12h20'),
        ('Book a Consultation', reverse('api:book'), 'M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z'),
        ('About Us', reverse('api:about'), 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z'),
        ('Health Library', reverse('health:index'), 'M12 2a3 3 0 013 3c0 1.5-1 2-1 3.5V10l4 4-1.5 1.5L14 13v4a3 3 0 01-2 2.83V22h-2v-2.17A3 3 0 018 17v-4l-2.5 2.5L4 14l4-4V8.5C7 7 6 6.5 6 5a3 3 0 016 0'),
        ('Herbal Products', reverse('api:products'), 'M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4'),
        ('Blog & Articles', reverse('api:blog'), 'M4 19.5A2.5 2.5 0 016.5 17H20M4 4.5A2.5 2.5 0 016.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15z'),
        ('Contact Us', reverse('api:contact'), 'M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z'),
    ]
    return render(request, 'home/index.html', {
        'featured_services': Service.objects.filter(active=True, is_featured=True)[:6],
        'featured_products': Product.objects.filter(active=True, is_featured=True)[:8],
        'live_promotions':   list(Promotion.live_qs()[:8]),
        'testimonials':      Testimonial.objects.filter(is_approved=True)[:6],
        'recent_posts':      BlogPost.objects.filter(is_published=True)[:3],
        'stats': {
            'services': Service.objects.filter(active=True).count(),
            'products': Product.objects.filter(active=True).count(),
        },
        'trust_indicators': TRUST_INDICATORS,
        'explore_links': explore_links,
        'conditions':        CONDITIONS,
    })


def services(request):
    category = request.GET.get('category', '')
    qs = Service.objects.filter(active=True)
    if category:
        qs = qs.filter(category=category)
    site = SiteSettings.get()
    return render(request, 'services/list.html', {
        'services': qs, 'active_category': category, 'categories': Service.CATEGORY_CHOICES,
        'page_title': f"Our Services | {site.site_name}",
        'page_description': f"Explore {site.site_name}'s traditional and herbal healthcare services.",
    })


def service_detail(request, slug):
    service = get_object_or_404(Service, slug=slug, active=True)
    related = Service.objects.filter(active=True, category=service.category).exclude(pk=service.pk)[:3]
    return render(request, 'services/detail.html', {
        'service': service, 'related': related,
        'page_title': f"{service.title} | {SiteSettings.get().site_name}",
        'page_description': service.short_description[:160],
    })


def products(request):
    site = SiteSettings.get()
    qs = Product.objects.filter(active=True).select_related('category')
    category_slug = request.GET.get('category', '')
    if category_slug:
        qs = qs.filter(category__slug=category_slug)

    # Promotions band: only ever shown when something is actually live —
    # no manual homepage/list editing needed as promotions start/end.
    live_promotions = list(Promotion.live_qs().filter(product__active=True))

    return render(request, 'products/list.html', {
        'products': qs,
        'categories': ProductCategory.objects.filter(is_active=True),
        'active_category': category_slug,
        'live_promotions': live_promotions,
        'page_title': f"Herbal Products | {site.site_name}",
        'page_description': f"Browse traditional herbal remedies from {site.site_name}.",
    })


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related('category').prefetch_related('gallery_images'),
        slug=slug, active=True
    )
    # Public shop = no prices; the enquiry form (and WhatsApp prefill) is the
    # conversion path. Prices are handled privately by the owner after the
    # enquiry lands in the dashboard.
    enquiry_form = ProductEnquiryForm(initial={
        'product_id': product.id,
        'product_name': product.title,
        'quantity': 1,
    })
    related = (Product.objects.filter(active=True, category=product.category)
               .exclude(pk=product.pk)[:4]) if product.category_id else Product.objects.none()
    gallery = _product_gallery(product)
    site = SiteSettings.get()
    return render(request, 'products/detail.html', {
        'product': product, 'form': AddToCartForm(),
        'enquiry_form': enquiry_form, 'gallery': gallery,
        'gallery_json': json.dumps(gallery),
        'related_products': related,
        'promotion': product.active_promotion,
        'page_title': f"{product.title} | {site.site_name}",
        'page_description': product.short_description[:160],
    })


@require_POST
def product_enquiry(request, slug):
    product = get_object_or_404(Product, slug=slug, active=True)
    form = ProductEnquiryForm(request.POST)
    if form.is_valid():
        qty = form.cleaned_data['quantity']
        message = form.cleaned_data['message'].strip()
        product_line = f"Product: {product.title} (quantity: {qty})\n"
        inquiry = form.save(commit=False)
        inquiry.message = product_line + message
        inquiry.save()
        create_notification(
            'inquiry', f'New Product Enquiry: {inquiry.name}',
            f'{inquiry.name} enquired about {product.title}',
            url=f"/dashboard/messages/{inquiry.pk}/",
        )
        wa_url = trigger_whatsapp_alert(build_inquiry_wa_message(inquiry))
        try:
            notify_new_product_enquiry(inquiry)
        except Exception:
            logger.exception(f'notify_new_product_enquiry failed for inquiry {inquiry.pk}')
        messages.success(request, 'Enquiry sent. We will reply with the price shortly.')
        return render(request, 'products/enquiry_success.html', {
            'product': product, 'inquiry': inquiry, 'wa_url': wa_url,
            'page_title': f"Enquiry Received | {SiteSettings.get().site_name}",
        })
    messages.warning(request, 'Please correct the errors below and try again.')
    related = (Product.objects.filter(active=True, category=product.category)
               .exclude(pk=product.pk)[:4]) if product.category_id else Product.objects.none()
    gallery = _product_gallery(product)
    site = SiteSettings.get()
    return render(request, 'products/detail.html', {
        'product': product, 'form': AddToCartForm(),
        'enquiry_form': form, 'gallery': gallery,
        'gallery_json': json.dumps(gallery),
        'related_products': related,
        'promotion': product.active_promotion,
        'page_title': f"{product.title} | {site.site_name}",
        'page_description': product.short_description[:160],
    })


def _product_gallery(product):
    """Flattens the main image + gallery rows into [{'url','alt'}, …] so the
    template never touches Cloudinary internals. Falls back to a placeholder."""
    from django.templatetags.static import static
    fallback = static('img/product-placeholder.jpg')
    items = []
    if product.image_url():
        items.append({'url': product.image_url(), 'alt': product.title})
    for img in product.gallery_images.all():
        items.append({'url': img.image.url, 'alt': img.alt_text or product.title})
    if not items:
        items.append({'url': fallback, 'alt': product.title})
    return items


@require_POST
def cart_add(request, slug):
    product = get_object_or_404(Product, slug=slug, active=True)
    form = AddToCartForm(request.POST)
    quantity = form.cleaned_data['quantity'] if form.is_valid() else 1

    # Server-side stock gate: a tracked product that's sold out cannot be
    # added even if the button was hidden client-side.
    if product.track_stock and product.stock_quantity is not None and product.stock_quantity <= 0:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'ok': False, 'error': 'This product is currently out of stock.'})
        messages.warning(request, 'This product is currently out of stock.')
        next_url = request.POST.get('next') or reverse('api:product_detail', args=[product.slug])
        return redirect(next_url)

    cart = get_cart(request)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product, defaults={'quantity': quantity})
    if not created:
        item.quantity += quantity

    item.quantity = _clamp_cart_quantity(product, item.quantity)
    item.save(update_fields=['quantity'])

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'ok': True,
            'added': product.title,
            'item_quantity': item.quantity,
            'cart_total': cart.total_items,
        })

    messages.success(request, f'Added {product.title} to your cart.')
    next_url = request.POST.get('next') or reverse('api:cart')
    return redirect(next_url)


def _clamp_cart_quantity(product, quantity):
    """Never let a cart exceed what's actually available when the product
    tracks stock — stock is (re)validated server-side at add & update time."""
    if not product.track_stock or product.stock_quantity is None:
        return max(int(quantity), 1)
    return max(1, min(int(quantity), product.stock_quantity))


def cart_view(request):
    cart = get_cart(request)
    site = SiteSettings.get()
    return render(request, 'products/cart.html', {
        'cart': cart,
        'page_title': f"Your Cart | {site.site_name}",
    })


@require_POST
def cart_update(request, item_id):
    cart = get_cart(request)
    item = get_object_or_404(CartItem, pk=item_id, cart=cart)
    try:
        quantity = int(request.POST.get('quantity', 1))
    except (TypeError, ValueError):
        quantity = 1
    if quantity < 1:
        item.delete()
        messages.success(request, 'Item removed from your cart.')
    else:
        item.quantity = _clamp_cart_quantity(item.product, quantity)
        item.save(update_fields=['quantity'])
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'ok': True, 'cart_total': cart.total_items})
    return redirect('api:cart')


@require_POST
def cart_remove(request, item_id):
    cart = get_cart(request)
    item = get_object_or_404(CartItem, pk=item_id, cart=cart)
    item.delete()
    messages.success(request, 'Item removed from your cart.')
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'ok': True, 'cart_total': cart.total_items})
    return redirect('api:cart')


def checkout(request):
    cart = get_cart(request)
    site = SiteSettings.get()
    if not cart or cart.total_items == 0:
        messages.warning(request, 'Your cart is empty.')
        return redirect('api:products')

    # Public WHATSAPP path: opens the customer's own WhatsApp with the cart
    # contents — items + quantities only, never prices.
    cart_wa_url = build_cart_whatsapp_url(cart)

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # Revalidate the whole cart before committing anything: a product
            # may have been deactivated or sold out since it was added.
            problems = []
            for cart_item in cart.item_list:
                p = cart_item.product
                if not p.active:
                    problems.append(f'{p.title} is no longer available.')
                elif p.track_stock and p.stock_quantity is not None and cart_item.quantity > p.stock_quantity:
                    problems.append(f'Only {p.stock_quantity} of {p.title} in stock right now.')
            if problems:
                messages.warning(request, 'Please review your cart: ' + ' '.join(problems))
                return redirect('api:cart')
            with transaction.atomic():
                order = form.save(commit=False)
                order.subtotal = cart.subtotal
                order.save()
                for cart_item in cart.item_list:
                    OrderItem.objects.create(
                        order=order, product=cart_item.product,
                        product_name=cart_item.product.title,
                        unit_price=cart_item.unit_price,
                        quantity=cart_item.quantity,
                    )
                cart.cart_items.all().delete()
            create_notification(
                'order', f'New Order: {order.order_number}',
                f'{order.customer_name} placed a new order',
                url=f"/dashboard/orders/{order.pk}/",
            )
            wa_url = trigger_whatsapp_alert(build_order_wa_message(order))
            # Owner/staff-facing email + WhatsApp Business alerts, gated by
            # Website Settings. The order is already saved regardless.
            try:
                notify_new_order(order)
            except Exception:
                logger.exception(f'notify_new_order failed for order {order.pk}')
            return render(request, 'products/order_success.html', {
                'order': order, 'wa_url': wa_url,
                'page_title': f"Order Received | {site.site_name}",
            })
        else:
            messages.warning(request, 'Please correct the errors below.')
    else:
        initial = {}
        if request.user.is_authenticated:
            initial['customer_name'] = request.user.get_full_name()
            initial['customer_email'] = request.user.email
        form = CheckoutForm(initial=initial)

    return render(request, 'products/checkout.html', {
        'cart': cart, 'form': form, 'cart_wa_url': cart_wa_url,
        'page_title': f"Checkout | {site.site_name}",
    })


def book(request):
    initial = {}
    service_slug = request.GET.get('service', '')
    if service_slug:
        try:
            initial['service'] = Service.objects.get(slug=service_slug, active=True)
        except Service.DoesNotExist:
            pass

    # Pre-fill if logged in
    if request.user.is_authenticated:
        initial.setdefault('contact_name', request.user.get_full_name())
        initial.setdefault('contact_email', request.user.email)
        try:
            initial.setdefault('contact_phone', request.user.patient_profile.phone)
        except ObjectDoesNotExist:
            pass  # user has no PatientProfile yet — nothing to prefill, not an error

    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            if request.user.is_authenticated:
                appointment.patient = getattr(request.user, 'patient_profile', None)
            appointment.save()
            create_notification(
                'appointment', f'New Appointment: {appointment.contact_name}',
                f'{appointment.contact_name} booked {appointment.service_name or "General Consultation"}',
                url=f"/dashboard/appointments/{appointment.pk}/",
            )
            wa_url = trigger_whatsapp_alert(build_appointment_wa_message(appointment))
            # Owner/staff-facing notifications -- independent email/WhatsApp
            # Business toggles live in Website Settings; booking is already
            # saved above regardless of what happens here.
            try:
                notify_new_booking(appointment)
            except Exception:
                logger.exception(f'notify_new_booking failed for appointment {appointment.pk}')
            # Confirmation email to the CUSTOMER (separate from the owner
            # notification above; always attempted, non-blocking).
            send_appointment_confirmation(appointment)
            messages.success(request, 'Your appointment has been booked. We will confirm shortly.')
            return render(request, 'booking/success.html', {
                'appointment': appointment, 'wa_url': wa_url,
                'booking_ref': f'PHB-{appointment.pk:06d}',
                'page_title': f"Booking Received | {SiteSettings.get().site_name}",
            })
        else:
            messages.warning(request, 'Please correct the errors below and try again.')
    else:
        form = AppointmentForm(initial=initial)

    site = SiteSettings.get()
    return render(request, 'booking/book.html', {
        'form': form,
        'is_guest': not request.user.is_authenticated,
        'page_title': f"Book a Session | {site.site_name}",
        'page_description': f"Book a healing appointment with {site.site_name} — guest booking allowed, no account required.",
    })


def blog(request):
    qs = BlogPost.objects.filter(is_published=True)
    category = request.GET.get('category', '')
    if category:
        qs = qs.filter(category=category)
    paginator = Paginator(qs, 9)
    page = paginator.get_page(request.GET.get('page'))
    categories = BlogPost.objects.filter(is_published=True).values_list('category', flat=True).distinct()
    site = SiteSettings.get()
    return render(request, 'blog/list.html', {
        'page_obj': page, 'categories': categories, 'active_category': category,
        'page_title': f"Healing Blog | {site.site_name}",
        'page_description': f"Healing wisdom, guides and traditional health insights from {site.site_name}.",
    })


def blog_detail(request, slug):
    post    = get_object_or_404(BlogPost, slug=slug, is_published=True)
    related = BlogPost.objects.filter(is_published=True).exclude(pk=post.pk)[:3]
    return render(request, 'blog/detail.html', {
        'post': post, 'related': related,
        'page_title': f"{post.title} | {SiteSettings.get().site_name}",
        'page_description': post.excerpt[:160],
    })


def about(request):
    site = SiteSettings.get()
    return render(request, 'about/index.html', {
        'testimonials': Testimonial.objects.filter(is_approved=True)[:3],
        'values': VALUES, 'hours': HOURS,
        'page_title': f"About Us | {site.site_name}",
        'page_description': site.about_description[:160],
    })


def contact(request):
    if request.method == 'POST':
        form = InquiryForm(request.POST)
        if form.is_valid():
            inquiry = form.save()
            create_notification(
                'inquiry', f'New Inquiry: {inquiry.name}', inquiry.message[:100],
                url=f"/dashboard/messages/{inquiry.pk}/",
            )
            wa_url = trigger_whatsapp_alert(build_inquiry_wa_message(inquiry))
            try:
                notify_new_inquiry(inquiry)
            except Exception:
                logger.exception(f'notify_new_inquiry failed for inquiry {inquiry.pk}')
            messages.success(request, 'Message sent. We will get back to you soon.')
            return render(request, 'contact/success.html', {
                'inquiry': inquiry, 'wa_url': wa_url,
                'page_title': f"Message Sent | {SiteSettings.get().site_name}",
            })
    else:
        form = InquiryForm()
    site = SiteSettings.get()
    return render(request, 'contact/index.html', {
        'form': form, 'hours': HOURS,
        'page_title': f"Contact Us | {site.site_name}",
        'page_description': f"Get in touch with {site.site_name} — phone, WhatsApp, email and location.",
    })


@require_POST
def subscribe(request):
    form = SubscriberForm(request.POST)
    if form.is_valid():
        sub, created = Subscriber.objects.get_or_create(email=form.cleaned_data['email'])
        if created:
            create_notification('subscriber', 'New Subscriber', sub.email)
        return JsonResponse({'ok': True, 'message': 'Subscribed! May healing find you.'})
    return JsonResponse({'ok': False, 'message': 'Invalid email address.'}, status=400)


def submit_testimonial(request):
    if request.method == 'POST':
        form = TestimonialForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Thank you! Your testimonial will appear after review.')
            return redirect('api:home')
    else:
        form = TestimonialForm()
    return render(request, 'testimonials/submit.html', {'form': form})


# ── ADMIN: APPOINTMENT CALENDAR (deprecated) ──────────────────────────────────
@staff_member_required
def admin_calendar(request):
    """
    Deprecated. The real appointment calendar now lives in the custom
    staff dashboard overview (/dashboard/), which is the single source of
    truth for appointment calendar data — this route now just redirects
    there instead of maintaining a second, separate calendar implementation.
    """
    return redirect('dashboard:overview')

# ── ADMIN: WHATSAPP REPLY TEMPLATES ───────────────────────────────────────────
@staff_member_required
def whatsapp_templates(request):
    """Pre-written WhatsApp reply templates for the admin to copy."""
    site = SiteSettings.get()
    templates = [
        {
            'title':    'Appointment Confirmed',
            'category': 'Appointments',
            'message':  f"Salaam! This is {site.site_name}. Your appointment has been CONFIRMED. We look forward to seeing you. May Allah grant you healing. ...healing hands, divine touch!",
        },
        {
            'title':    'Appointment Reminder',
            'category': 'Appointments',
            'message':  f"Salaam! A reminder from {site.site_name} about your upcoming appointment. Please arrive 10 minutes early. Call us on {site.contact_phone} for any changes. Jazakallahu khairan.",
        },
        {
            'title':    'Appointment Rescheduled',
            'category': 'Appointments',
            'message':  f"Salaam! We need to reschedule your appointment at {site.site_name}. Please call us on {site.contact_phone} or reply here to agree on a new time. We apologise for any inconvenience.",
        },
        {
            'title':    'Appointment Cancelled',
            'category': 'Appointments',
            'message':  f"Salaam! Your appointment at {site.site_name} has been cancelled. Please contact us on {site.contact_phone} to rebook at your convenience. We are sorry for any inconvenience.",
        },
        {
            'title':    'Order Received — Contact for Delivery',
            'category': 'Product Orders',
            'message':  f"Salaam! Thank you for your order from {site.site_name}. We have received it and will contact you shortly to arrange payment and delivery. Jazakallahu khairan.",
        },
        {
            'title':    'Order Ready for Pickup',
            'category': 'Product Orders',
            'message':  f"Salaam! Your herbal product order from {site.site_name} is READY. You can pick it up at {site.address}. Opening hours: Mon–Sat 8am–6pm. Please bring this message. ...healing hands, divine touch!",
        },
        {
            'title':    'General Inquiry Response',
            'category': 'Inquiries',
            'message':  f"Salaam! Thank you for contacting {site.site_name}. We have received your message and will respond within 24 hours. For urgent matters please call {site.contact_phone}. Jazakallahu khairan.",
        },
        {
            'title':    'Treatment Follow-Up',
            'category': 'Follow-Up',
            'message':  f"Salaam! This is {site.site_name} checking in. How are you feeling after your treatment? We hope you are experiencing healing and improvement. Do not hesitate to reach out if you need anything. WE CURE, ALLAH HEALS.",
        },
        {
            'title':    'Directions to the Clinic',
            'category': 'General',
            'message':  f"Salaam! {site.site_name} is located at: {site.address}. Nearest landmark: Iyana-ipaja area. Call {site.contact_phone} when you are close and we will guide you. ...healing hands, divine touch!",
        },
        {
            'title':    'Prayer & Spiritual Consultation Info',
            'category': 'General',
            'message':  f"Salaam! For spiritual consultation and prayer assistance at {site.site_name}, please book an appointment or visit us at {site.address}. Sessions are by appointment. Call {site.contact_phone} to schedule. WE CURE, ALLAH HEALS.",
        },
    ]
    return render(request, 'calendar/whatsapp_templates.html', {
        'templates': templates, 'site': site
    })


# ── ADMIN: APPOINTMENT RECEIPT PDF ────────────────────────────────────────────
@staff_member_required
def admin_appointment_pdf(request, pk):
    """Admin can print/download any appointment receipt."""
    appointment = get_object_or_404(Appointment, pk=pk)
    site = SiteSettings.get()
    html = render(request, 'pdf/appointment_receipt.html', {
        'appointment': appointment, 'site': site, 'now': timezone.now(),
    }).content
    try:
        from xhtml2pdf import pisa
        from io import BytesIO
        buf = BytesIO()
        pisa.CreatePDF(html.decode('utf-8'), dest=buf)
        buf.seek(0)
        response = HttpResponse(buf, content_type='application/pdf')
        response['Content-Disposition'] = f'filename="receipt_{pk}.pdf"'
        return response
    except Exception:
        logger.exception(f'Appointment receipt PDF generation failed for appointment {pk}')
        messages.error(request, 'We could not generate the PDF right now. Please try again.')
        return redirect('dashboard:appointment_detail', pk=pk)
