from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Q, Count
from django.utils import timezone
from django.views.decorators.http import require_POST
from datetime import date

from api.models import (
    Appointment, Inquiry, Notification, Order, Service, Product,
    ProductCategory, Promotion, BlogPost, Testimonial, Subscriber, SiteSettings,
)
from api.utils import (
    create_notification, trigger_whatsapp_alert, build_appointment_wa_message,
)
from api import whatsapp_service
from api.permissions import has_dashboard_access, has_dashboard_section, dashboard_sections, is_staff_owner
from api.email_service import send_appointment_status_update
from accounts.models import PatientProfile
from .models import StaffAccess, TwoFactorAuth
from . import two_factor as two_factor_service
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

from .auth import staff_required, section_required, owner_required


def _badge_counts():
    return {
        'unread_notifications_count': Notification.objects.filter(is_read=False).count(),
        'unread_messages_count': Inquiry.objects.filter(is_read=False).count(),
    }


# ── AUTH ──────────────────────────────────────────────────────────────────────
def dashboard_login(request):
    if request.user.is_authenticated and has_dashboard_access(request.user):
        return redirect('dashboard:overview')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if not has_dashboard_access(user):
                messages.error(request, "This account doesn't have staff dashboard access.")
            else:
                next_url = request.GET.get('next') or request.POST.get('next') or ''
                if not url_has_allowed_host_and_scheme(
                        url=next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
                    next_url = ''
                two_factor = getattr(user, 'two_factor', None)
                if two_factor and two_factor.is_enabled:
                    # Password verified, but don't fully log in yet -- a
                    # pending-user marker in the session, checked again by
                    # two_factor_challenge, stands in for the login until a
                    # valid TOTP/recovery code is also provided.
                    request.session['2fa_pending_user_id'] = user.pk
                    request.session['2fa_next_url'] = next_url
                    return redirect('dashboard:two_factor_challenge')
                auth_login(request, user)
                return redirect(next_url or 'dashboard:overview')
        else:
            messages.error(request, 'Invalid staff username/email or password.')
    else:
        form = AuthenticationForm(request)

    return render(request, 'dashboard/login.html', {'form': form})


def two_factor_challenge(request):
    """
    Second login step for accounts with 2FA enabled. Only reachable via
    the '2fa_pending_user_id' session marker dashboard_login sets after
    verifying the password -- there is no way to reach a logged-in state
    here without both factors.
    """
    pending_user_id = request.session.get('2fa_pending_user_id')
    if not pending_user_id:
        return redirect('dashboard:login')

    user = User.objects.filter(pk=pending_user_id).first()
    two_factor = getattr(user, 'two_factor', None) if user else None
    if not user or not two_factor or not two_factor.is_enabled:
        # Fail safe back to a normal login rather than ever letting a
        # stale/tampered session bypass 2FA.
        request.session.pop('2fa_pending_user_id', None)
        request.session.pop('2fa_next_url', None)
        return redirect('dashboard:login')

    if request.method == 'POST':
        code = request.POST.get('code', '')
        use_recovery = request.POST.get('use_recovery') == '1'
        verified = (
            two_factor.verify_and_consume_recovery_code(code) if use_recovery
            else two_factor_service.verify_code(two_factor.secret, code)
        )
        if verified:
            next_url = request.session.pop('2fa_next_url', '') or 'dashboard:overview'
            request.session.pop('2fa_pending_user_id', None)
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            auth_login(request, user)
            if use_recovery:
                messages.warning(
                    request,
                    'You signed in with a recovery code, which is now used up. '
                    'Consider regenerating your recovery codes from Account & Security.'
                )
            return redirect(next_url)
        messages.error(request, 'Invalid code. Please try again.')

    return render(request, 'dashboard/two_factor_challenge.html', {'username': user.username})


@staff_required
def dashboard_logout(request):
    auth_logout(request)
    messages.success(request, 'Signed out of the staff dashboard.')
    return redirect('dashboard:login')


def _build_overview_calendar(request):
    """
    Real appointment calendar for the dashboard overview. One query per
    month (not per day), grouped in Python by date. 'Upcoming' = pending or
    confirmed appointments today or in the future -- matches the project's
    real Appointment.STATUS_CHOICES, no separate status system.
    """
    import calendar as cal_module

    today = timezone.localdate()
    try:
        year = int(request.GET.get('cal_year', today.year))
    except (TypeError, ValueError):
        year = today.year
    try:
        month = int(request.GET.get('cal_month', today.month))
    except (TypeError, ValueError):
        month = today.month
    if not (1 <= month <= 12):
        month = today.month
    year = max(1900, min(2200, year))

    first_of_month = date(year, month, 1)
    if month == 12:
        next_month_first, next_year, next_month = date(year + 1, 1, 1), year + 1, 1
    else:
        next_month_first, next_year, next_month = date(year, month + 1, 1), year, month + 1
    if month == 1:
        prev_year, prev_month = year - 1, 12
    else:
        prev_year, prev_month = year, month - 1

    range_start = max(first_of_month, today)  # only "upcoming" (today or later) counts
    appts = (Appointment.objects
             .filter(status__in=['pending', 'confirmed'],
                     appointment_date__gte=range_start,
                     appointment_date__lt=next_month_first)
             .select_related('service', 'patient')
             .order_by('appointment_date', 'preferred_time'))

    by_date = {}
    for a in appts:
        key = a.appointment_date.isoformat()
        by_date.setdefault(key, []).append({
            'id': a.pk,
            'time': a.preferred_time or 'TBC',
            'name': a.contact_name,
            'service': a.service_name or 'General Consultation',
            'status': a.status,
            'status_display': a.get_status_display(),
            'detail_url': reverse('dashboard:appointment_detail', args=[a.pk]),
        })

    weeks = []
    for week in cal_module.Calendar(firstweekday=6).monthdatescalendar(year, month):
        row = []
        for d in week:
            iso = d.isoformat()
            row.append({
                'date': d, 'day': d.day, 'iso': iso,
                'in_month': d.month == month,
                'is_today': d == today,
                'appointments': by_date.get(iso, []),
                'count': len(by_date.get(iso, [])),
            })
        weeks.append(row)

    return {
        'cal_weeks': weeks,
        'cal_month_name': cal_module.month_name[month],
        'cal_year': year,
        'cal_month': month,
        'cal_today': today,
        'cal_prev_year': prev_year, 'cal_prev_month': prev_month,
        'cal_next_year': next_year, 'cal_next_month': next_month,
        'cal_data_json': by_date,
        'cal_day_names': ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
    }


# ── OVERVIEW ──────────────────────────────────────────────────────────────────
@staff_required
def overview(request):
    today = timezone.localdate()
    month_start = today.replace(day=1)

    stats = {
        'total_appointments':     Appointment.objects.count(),
        'pending_appointments':   Appointment.objects.filter(status='pending').count(),
        'today_appointments':     Appointment.objects.filter(appointment_date=today).count(),
        'completed_this_month':   Appointment.objects.filter(
            status='completed', updated_at__date__gte=month_start).count(),
        'unread_messages':        Inquiry.objects.filter(is_read=False).count(),
        'new_orders':             Order.objects.filter(status='pending').count(),
        'active_promotions':      sum(1 for p in Promotion.objects.select_related('product') if p.is_live),
        'low_stock_products':     Product.objects.filter(track_stock=True, stock_quantity__lte=5, active=True).count(),
        'unread_notifications':   Notification.objects.filter(is_read=False).count(),
    }

    top_services = (Appointment.objects
                    .exclude(service_name='')
                    .values('service_name')
                    .annotate(bookings=Count('id'))
                    .order_by('-bookings')[:5])

    context = {
        'active_nav': 'overview',
        'stats': stats,
        'recent_appointments': Appointment.objects.select_related('service').order_by('-created_at')[:6],
        'recent_notifications': Notification.objects.order_by('-created_at')[:6],
        'recent_messages': Inquiry.objects.order_by('-created_at')[:5],
        'top_services': top_services,
        **_badge_counts(),
    }
    context.update(_build_overview_calendar(request))
    return render(request, 'dashboard/overview.html', context)


# ── APPOINTMENTS ──────────────────────────────────────────────────────────────
@section_required('appointments')
def appointments_list(request):
    qs = Appointment.objects.select_related('service', 'patient').order_by('-created_at')
    status = request.GET.get('status', '')
    q = request.GET.get('q', '').strip()
    if status:
        qs = qs.filter(status=status)
    if q:
        qs = qs.filter(Q(contact_name__icontains=q) | Q(contact_phone__icontains=q) |
                        Q(contact_email__icontains=q))
    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'dashboard/appointments_list.html', {
        'active_nav': 'appointments',
        'page_obj': page, 'active_status': status, 'q': q,
        'status_choices': Appointment.STATUS_CHOICES,
        **_badge_counts(),
    })


@section_required('appointments')
def appointment_detail(request, pk):
    appointment = get_object_or_404(Appointment.objects.select_related('service', 'patient'), pk=pk)
    return render(request, 'dashboard/appointment_detail.html', {
        'active_nav': 'appointments',
        'appointment': appointment,
        'wa_url': trigger_whatsapp_alert(build_appointment_wa_message(appointment)),
        **_badge_counts(),
    })


@section_required('appointments')
@require_POST
def appointment_update_status(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    new_status = request.POST.get('status')

    if new_status not in dict(Appointment.STATUS_CHOICES):
        messages.error(request, 'Invalid status.')
        return redirect('dashboard:appointment_detail', pk=pk)

    # Backend is the source of truth for conflicts — never trust the frontend alone.
    if new_status == 'confirmed':
        appointment.status = 'confirmed'
        if appointment.conflicts_with_confirmed():
            messages.warning(
                request,
                'This time slot is already confirmed for another appointment. Please choose '
                'another time before confirming.'
            )
            appointment.refresh_from_db(fields=['status'])
            return redirect('dashboard:appointment_detail', pk=pk)

    appointment.status = new_status
    try:
        with transaction.atomic():
            appointment.save()
    except IntegrityError:
        # The Python check above already passed, but another staff member's
        # confirmation committed in the gap between that check and this
        # save -- the database-level constraint is the real backstop here.
        # Wrapping the save in its own atomic block/savepoint means this
        # failure rolls back cleanly on PostgreSQL too, instead of poisoning
        # the rest of the request's transaction.
        logger.warning(f'Confirmed-slot race condition caught for appointment {pk}')
        messages.error(
            request,
            'This appointment slot was just taken by another appointment. Please choose another time.'
        )
        return redirect('dashboard:appointment_detail', pk=pk)

    try:
        send_appointment_status_update(appointment)
    except Exception:
        logger.exception(f'Failed to send status-update email for appointment {appointment.pk}')

    if new_status == 'confirmed':
        create_notification('appointment', f'Appointment confirmed: {appointment.contact_name}',
                            f"{appointment.contact_name}'s appointment was confirmed.")
    elif new_status == 'cancelled':
        create_notification('appointment', f'Appointment cancelled: {appointment.contact_name}',
                            f"{appointment.contact_name}'s appointment was cancelled.")

    messages.success(request, f'Appointment marked as {appointment.get_status_display()}.')
    return redirect('dashboard:appointment_detail', pk=pk)


# ── PATIENTS ──────────────────────────────────────────────────────────────────
@section_required('orders')
def patients_list(request):
    q = request.GET.get('q', '').strip()
    qs = PatientProfile.objects.select_related('user').order_by('-created_at')
    if q:
        qs = qs.filter(Q(user__first_name__icontains=q) | Q(user__last_name__icontains=q) |
                        Q(user__email__icontains=q) | Q(phone__icontains=q))
    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'dashboard/patients_list.html', {
        'active_nav': 'patients',
        'page_obj': page, 'q': q,
        **_badge_counts(),
    })


@section_required('orders')
def patient_detail(request, pk):
    patient = get_object_or_404(PatientProfile.objects.select_related('user'), pk=pk)
    # Medical notes are only ever rendered here, behind @staff_required — never
    # on public pages, WhatsApp messages, or patient-facing confirmations.
    return render(request, 'dashboard/patient_detail.html', {
        'active_nav': 'patients',
        'patient': patient,
        'appointments': patient.appointments,
        **_badge_counts(),
    })


# ── MESSAGES / INQUIRIES ──────────────────────────────────────────────────────
@section_required('messages')
def messages_list(request):
    qs = Inquiry.objects.order_by('-created_at')
    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'dashboard/messages_list.html', {
        'active_nav': 'messages',
        'page_obj': page,
        **_badge_counts(),
    })


@section_required('messages')
def message_detail(request, pk):
    inquiry = get_object_or_404(Inquiry, pk=pk)
    if not inquiry.is_read:
        inquiry.is_read = True
        inquiry.save(update_fields=['is_read'])
    return render(request, 'dashboard/message_detail.html', {
        'active_nav': 'messages',
        'inquiry': inquiry,
        **_badge_counts(),
    })


# ── NOTIFICATIONS ─────────────────────────────────────────────────────────────
@staff_required
def notifications_list(request):
    qs = Notification.objects.order_by('-created_at')
    paginator = Paginator(qs, 25)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'dashboard/notifications_list.html', {
        'active_nav': 'notifications',
        'page_obj': page,
        **_badge_counts(),
    })


@staff_required
@require_POST
def notification_mark_read(request, pk):
    notif = get_object_or_404(Notification, pk=pk)
    notif.is_read = True
    notif.save(update_fields=['is_read'])
    return redirect(request.POST.get('next') or 'dashboard:notifications')


@staff_required
@require_POST
def notifications_mark_all_read(request):
    Notification.objects.filter(is_read=False).update(is_read=True)
    messages.success(request, 'All notifications marked as read.')
    return redirect('dashboard:notifications')


# ── PWA: MANIFEST + SERVICE WORKER (PUBLIC) ──────────────────────────────────
# These must reply 200 to the browser WITHOUT requiring a login, otherwise
# installability and the service worker would break (the browser would get a
# 302-to-login instead of the manifest/SW, or silently re-login). The SW only
# caches assets and NEVER intercepts authenticated dashboard HTML, so nothing
# sensitive can be leaked offline. Scope is /dashboard/ only.
def pwa_manifest(request):
    from django.http import JsonResponse
    from django.templatetags.static import static
    site = SiteSettings.get()
    origin = request.build_absolute_uri('/')
    site_name = (site.site_name or 'Faralokun Vital Herbs').strip()
    short = (site_name[:19]).strip() if site_name else 'Faralokun'
    return JsonResponse({
        "name": site_name,
        "short_name": short,
        "description": site.tagline or site_name,
        "start_url": origin + 'dashboard/',
        "scope": origin + 'dashboard/',
        "display": "standalone",
        "orientation": "portrait-primary",
        "background_color": "#13231B",
        "theme_color": "#3A7D44",
        "icons": [
            {'src': static('img/icon-192.png'), 'sizes': '192x192', 'type': 'image/png', 'purpose': 'any'},
            {'src': static('img/icon-512.png'), 'sizes': '512x512', 'type': 'image/png', 'purpose': 'any'},
            {'src': static('img/icon-maskable-512.png'), 'sizes': '512x512', 'type': 'image/png', 'purpose': 'maskable'},
        ],
    })


def pwa_service_worker(request):
    """
    Serves dashboard-sw.js from static so it can be a plain file manageable
    in the repo while still being versioned through Django's static pipeline.
    """
    from django.http import HttpResponse
    from django.contrib.staticfiles import finders
    path = finders.find('js/dashboard-sw.js')
    if path:
        import io
        with io.open(path, 'r', encoding='utf-8') as f:
            return HttpResponse(f.read(), content_type='application/javascript')
    return HttpResponse('self.addEventListener("install", function(event) { self.skipWaiting(); });',
                        content_type='application/javascript')


# ── WEB PUSH: DEVICE REGISTRATION + DELIVERY (STAFF ONLY) ────────────────────
def _json_response(data, status=200):
    from django.http import JsonResponse
    return JsonResponse(data, status=status)


@staff_required
def push_settings(request):
    """Current push state for this staff member: whether VAPID is configured,
    the (public-only) key the browser needs, and defaults for sound."""
    from django.templatetags.static import static
    from api.push_service import is_configured, subscription_count
    site = SiteSettings.get()
    return _json_response({
        'configured': is_configured(),
        'vapid_public_key': settings.VAPID_PUBLIC_KEY,
        'subscriptions': subscription_count(),
        'sound_enabled': site.notification_sound_enabled,
        'sound': site.notification_sound,
        'swap_icon': static('img/fv-mark.png'),
        'swap_badge': static('img/fv-mark.png'),
    }, status=200)


@staff_required
@require_POST
def push_subscribe(request):
    from api.models import PushSubscription
    endpoint = (request.POST.get('endpoint') or '').strip()
    p256dh = (request.POST.get('p256dh') or '').strip()
    auth = (request.POST.get('auth') or '').strip()
    if not (endpoint and p256dh and auth):
        return _json_response({'ok': False, 'error': 'Missing subscription details.'}, status=400)
    if len(endpoint) > 500:
        return _json_response({'ok': False, 'error': 'Endpoint too long.'}, status=400)
    try:
        PushSubscription.objects.update_or_create(
            endpoint=endpoint,
            defaults={'user': request.user, 'p256dh': p256dh, 'auth': auth},
        )
    except (IntegrityError, ValueError):
        return _json_response({'ok': False, 'error': 'Could not save subscription.'}, status=400)
    messages.success(request, 'Push notifications enabled for this device.')
    return _json_response({'ok': True, 'subscriptions': PushSubscription.objects.filter(user=request.user).count()})


@staff_required
@require_POST
def push_unsubscribe(request):
    from api.models import PushSubscription
    endpoint = (request.POST.get('endpoint') or '').strip()
    deleted, _ = PushSubscription.objects.filter(user=request.user, endpoint=endpoint).delete()
    if deleted:
        messages.info(request, 'Push notifications disabled for this device.')
        return _json_response({'ok': True})
    return _json_response({'ok': False, 'error': 'Subscription not found.'}, status=404)


@staff_required
@require_POST
def push_test(request):
    """Sends a test push to every device this staff member has registered."""
    from api.push_service import send_to_user, is_configured
    if not is_configured():
        messages.warning(
            request,
            'Push is not configured yet. Add VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY and '
            'VAPID_CLAIMS_EMAIL to the server .env to enable push notifications.')
        return _json_response({'ok': False, 'error': 'VAPID keys not configured.'}, status=400)
    result = send_to_user(
        request.user,
        'Test Push Notification',
        'Push notifications are working. You can now switch off this tab — alerts will still reach you.',
        url='/dashboard/notifications/',
    )
    if result['devices'] == 0:
        messages.warning(request, 'No subscribed devices for your account yet — enable notifications first.')
        return _json_response({'ok': False, 'error': 'No subscribed devices.'}, status=400)
    # Bell + broadcast confirmation are left out: this is a quiet self-test.
    messages.success(request, f"Test push sent to {result['sent']} device(s).")
    return _json_response({'ok': result['failed'] == 0, 'result': result})


# ── ORDERS ────────────────────────────────────────────────────────────────────
@section_required('orders')
def orders_list(request):
    qs = Order.objects.prefetch_related('items').order_by('-created_at')
    status = request.GET.get('status', '')
    q = request.GET.get('q', '').strip()
    if status:
        qs = qs.filter(status=status)
    if q:
        qs = qs.filter(Q(order_number__icontains=q) | Q(customer_name__icontains=q) | Q(customer_phone__icontains=q))
    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'dashboard/orders_list.html', {
        'active_nav': 'orders',
        'page_obj': page, 'active_status': status, 'q': q,
        'status_choices': Order.STATUS_CHOICES,
        **_badge_counts(),
    })


@section_required('orders')
def order_detail(request, pk):
    order = get_object_or_404(Order.objects.prefetch_related('items'), pk=pk)
    return render(request, 'dashboard/order_detail.html', {
        'active_nav': 'orders', 'order': order,
        'status_choices': Order.STATUS_CHOICES,
        **_badge_counts(),
    })


@section_required('orders')
@require_POST
def order_update_status(request, pk):
    order = get_object_or_404(Order, pk=pk)
    new_status = request.POST.get('status')
    if new_status in dict(Order.STATUS_CHOICES):
        order.status = new_status
        order.save(update_fields=['status', 'updated_at'])
        messages.success(request, f'Order marked as {order.get_status_display()}.')
    next_url = request.POST.get('next')
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)
    return redirect('dashboard:orders')


# ── CATALOG (services / products / blog / testimonials / subscribers) ─
# Full editing (images, rich text) stays in Django admin for now — linked
# directly from each row — while browsing, search, and quick status toggles
# live here in the dashboard.
@section_required('content')
def services_list(request):
    return render(request, 'dashboard/services_list.html', {
        'active_nav': 'services',
        'services': Service.objects.order_by('sort_order', 'title'),
        **_badge_counts(),
    })


@section_required('content')
def service_edit(request, pk=None):
    from .forms import ServiceForm
    instance = get_object_or_404(Service, pk=pk) if pk else None
    if request.method == 'POST':
        form = ServiceForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, f'Service {"updated" if pk else "created"}.')
            return redirect('dashboard:services')
        else:
            messages.warning(request, 'Please correct the errors below.')
    else:
        form = ServiceForm(instance=instance)
    return render(request, 'dashboard/service_form.html', {
        'active_nav': 'services', 'form': form, 'is_edit': bool(pk),
        **_badge_counts(),
    })


@section_required('products')
def categories_list(request):
    return render(request, 'dashboard/categories_list.html', {
        'active_nav': 'categories',
        'categories': ProductCategory.objects.annotate(product_count=Count('products')).order_by('sort_order', 'name'),
        **_badge_counts(),
    })


@section_required('products')
def category_edit(request, pk=None):
    from .forms import ProductCategoryForm
    instance = get_object_or_404(ProductCategory, pk=pk) if pk else None
    if request.method == 'POST':
        form = ProductCategoryForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, f'Category {"updated" if pk else "created"}.')
            return redirect('dashboard:categories')
        else:
            messages.warning(request, 'Please correct the errors below.')
    else:
        form = ProductCategoryForm(instance=instance)
    return render(request, 'dashboard/category_form.html', {
        'active_nav': 'categories', 'form': form, 'is_edit': bool(pk),
        **_badge_counts(),
    })


@section_required('products')
def products_list(request):
    qs = Product.objects.select_related('category').order_by('sort_order', 'title')
    q = request.GET.get('q', '').strip()
    category = request.GET.get('category', '')
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(short_description__icontains=q))
    if category:
        qs = qs.filter(category_id=category)
    return render(request, 'dashboard/products_list.html', {
        'active_nav': 'products',
        'products': qs, 'q': q, 'active_category': category,
        'categories': ProductCategory.objects.all(),
        **_badge_counts(),
    })


@section_required('products')
def product_edit(request, pk=None):
    from django.forms import inlineformset_factory
    from .forms import ProductForm
    from api.models import ProductImage
    instance = get_object_or_404(Product, pk=pk) if pk else None
    ImageFormSet = inlineformset_factory(
        Product, ProductImage, fields=['image', 'alt_text', 'sort_order'], extra=2, can_delete=True
    )
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=instance)
        formset = ImageFormSet(request.POST, request.FILES, instance=instance)
        if form.is_valid() and formset.is_valid():
            product = form.save()
            formset.instance = product
            formset.save()
            messages.success(request, f'Product {"updated" if pk else "created"}.')
            return redirect('dashboard:products')
        else:
            messages.warning(request, 'Please correct the errors below.')
    else:
        form = ProductForm(instance=instance)
        formset = ImageFormSet(instance=instance)
    return render(request, 'dashboard/product_form.html', {
        'active_nav': 'products', 'form': form, 'formset': formset, 'is_edit': bool(pk),
        **_badge_counts(),
    })


@section_required('products')
def promotions_list(request):
    now = timezone.now()
    return render(request, 'dashboard/promotions_list.html', {
        'active_nav': 'promotions',
        'promotions': Promotion.objects.select_related('product').order_by('-is_featured', '-start_date'),
        'now': now,
        **_badge_counts(),
    })


@section_required('products')
def promotion_edit(request, pk=None):
    from .forms import PromotionForm
    instance = get_object_or_404(Promotion, pk=pk) if pk else None
    if request.method == 'POST':
        form = PromotionForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, f'Promotion {"updated" if pk else "created"}.')
            return redirect('dashboard:promotions')
        else:
            messages.warning(request, 'Please correct the errors below.')
    else:
        form = PromotionForm(instance=instance)
    return render(request, 'dashboard/promotion_form.html', {
        'active_nav': 'promotions', 'form': form, 'is_edit': bool(pk),
        **_badge_counts(),
    })


@section_required('content')
def blog_list(request):
    return render(request, 'dashboard/blog_list.html', {
        'active_nav': 'blog',
        'posts': BlogPost.objects.order_by('-created_at'),
        **_badge_counts(),
    })


@section_required('content')
def blog_edit(request, pk=None):
    from .forms import BlogPostForm
    instance = get_object_or_404(BlogPost, pk=pk) if pk else None
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, f'Post {"updated" if pk else "published"}.')
            return redirect('dashboard:blog')
        else:
            messages.warning(request, 'Please correct the errors below.')
    else:
        form = BlogPostForm(instance=instance)
    return render(request, 'dashboard/blog_form.html', {
        'active_nav': 'blog', 'form': form, 'is_edit': bool(pk),
        **_badge_counts(),
    })


# ── HEALTH LIBRARY (Anatomy / Conditions / Herbs) ────────────────────────────
@section_required('content')
def health_anatomy_list(request):
    from health.models import AnatomyTopic
    return render(request, 'dashboard/health_anatomy_list.html', {
        'active_nav': 'health_anatomy',
        'topics': AnatomyTopic.objects.order_by('system', 'sort_order', 'name'),
        **_badge_counts(),
    })


@section_required('content')
def health_anatomy_edit(request, pk=None):
    from health.models import AnatomyTopic
    from .forms import AnatomyTopicForm
    instance = get_object_or_404(AnatomyTopic, pk=pk) if pk else None
    if request.method == 'POST':
        form = AnatomyTopicForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, f'Anatomy topic {"updated" if pk else "created"}.')
            return redirect('dashboard:health_anatomy')
        else:
            messages.warning(request, 'Please correct the errors below.')
    else:
        form = AnatomyTopicForm(instance=instance)
    return render(request, 'dashboard/health_anatomy_form.html', {
        'active_nav': 'health_anatomy', 'form': form, 'is_edit': bool(pk),
        **_badge_counts(),
    })


@section_required('content')
def health_conditions_list(request):
    from health.models import HealthCondition
    return render(request, 'dashboard/health_conditions_list.html', {
        'active_nav': 'health_conditions',
        'conditions': HealthCondition.objects.order_by('sort_order', 'name'),
        **_badge_counts(),
    })


@section_required('content')
def health_condition_edit(request, pk=None):
    from health.models import HealthCondition
    from .forms import HealthConditionForm
    instance = get_object_or_404(HealthCondition, pk=pk) if pk else None
    if request.method == 'POST':
        form = HealthConditionForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, f'Health condition {"updated" if pk else "created"}.')
            return redirect('dashboard:health_conditions')
        else:
            messages.warning(request, 'Please correct the errors below.')
    else:
        form = HealthConditionForm(instance=instance)
    return render(request, 'dashboard/health_condition_form.html', {
        'active_nav': 'health_conditions', 'form': form, 'is_edit': bool(pk),
        **_badge_counts(),
    })


@section_required('content')
def health_herbs_list(request):
    from health.models import Herb
    return render(request, 'dashboard/health_herbs_list.html', {
        'active_nav': 'health_herbs',
        'herbs': Herb.objects.order_by('sort_order', 'common_name'),
        **_badge_counts(),
    })


@section_required('content')
def health_herb_edit(request, pk=None):
    from health.models import Herb
    from .forms import HerbForm
    instance = get_object_or_404(Herb, pk=pk) if pk else None
    if request.method == 'POST':
        form = HerbForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, f'Herb {"updated" if pk else "created"}.')
            return redirect('dashboard:health_herbs')
        else:
            messages.warning(request, 'Please correct the errors below.')
    else:
        form = HerbForm(instance=instance)
    return render(request, 'dashboard/health_herb_form.html', {
        'active_nav': 'health_herbs', 'form': form, 'is_edit': bool(pk),
        **_badge_counts(),
    })


@section_required('content')
def testimonials_list(request):
    return render(request, 'dashboard/testimonials_list.html', {
        'active_nav': 'testimonials',
        'testimonials': Testimonial.objects.order_by('-created_at'),
        **_badge_counts(),
    })


@section_required('content')
@require_POST
def testimonial_toggle_approved(request, pk):
    t = get_object_or_404(Testimonial, pk=pk)
    t.is_approved = not t.is_approved
    t.save(update_fields=['is_approved'])
    return redirect('dashboard:testimonials')


@section_required('messages')
def subscribers_list(request):
    qs = Subscriber.objects.order_by('-subscribed_at')
    paginator = Paginator(qs, 40)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'dashboard/subscribers_list.html', {
        'active_nav': 'subscribers',
        'page_obj': page,
        **_badge_counts(),
    })


# ── SITE SETTINGS ─────────────────────────────────────────────────────────────
@section_required('settings')
def site_settings(request):
    from .forms import SiteSettingsForm
    site = SiteSettings.get()

    if request.method == 'POST':
        test_action = request.POST.get('test_action', '')
        if test_action:
            return _handle_notification_test(request, test_action)
        form = SiteSettingsForm(request.POST, request.FILES, instance=site)
        if form.is_valid():
            form.save()
            messages.success(request, 'Site settings updated.')
            return redirect('dashboard:site_settings')
        else:
            messages.warning(request, 'Please correct the errors below.')
    else:
        form = SiteSettingsForm(instance=site)
    return render(request, 'dashboard/site_settings.html', {
        'active_nav': 'settings',
        'form': form,
        'whatsapp_api_configured': whatsapp_service.is_configured(),
        'push_configured': (settings.VAPID_PUBLIC_KEY and settings.VAPID_PRIVATE_KEY),
        **_badge_counts(),
    })


def _handle_notification_test(request, action):
    """Site Settings 'Send test …' buttons. All of them redirect back with a
    clear message; they never raise into the UI."""
    site = SiteSettings.get()

    if action == 'test_email':
        from api.email_service import send_test_email
        recipient = (request.POST.get('test_recipient') or site.contact_email or '').strip()
        if not recipient:
            messages.error(request, 'Set a Contact Email or enter a recipient in the test box first.')
        elif send_test_email(recipient):
            messages.success(request, f'Test email sent to {recipient} — check the inbox (and spam folder).')
        else:
            messages.error(request, 'Test email failed. Verify host, port, user, password and TLS in the server .env.')
        return redirect('dashboard:site_settings')

    if action == 'test_whatsapp':
        number = site.effective_notification_whatsapp or site.effective_booking_whatsapp
        if not whatsapp_service.is_configured():
            messages.error(request,
                           'WhatsApp Business API is not configured on this server '
                           '(WHATSAPP_BUSINESS_API_TOKEN / WHATSAPP_BUSINESS_PHONE_NUMBER_ID in .env).')
        elif not number:
            messages.error(request, 'Set a WhatsApp Number in Contact Settings first.')
        else:
            sent, detail = whatsapp_service.send_business_whatsapp_message(
                number, f'Test notification from {site.site_name}. Notifications via WhatsApp are working.')
            if sent:
                messages.success(request, f'Test WhatsApp message sent to +{number}.')
            else:
                messages.error(request, f'Test WhatsApp message failed: {detail}')
        return redirect('dashboard:site_settings')

    if action == 'test_push':
        from api.push_service import send_to_user, is_configured
        if not is_configured():
            messages.error(request,
                           'Push is not configured. Add VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY and '
                           'VAPID_CLAIMS_EMAIL to the server .env to enable push notifications.')
        else:
            push_result = send_to_user(
                request.user,
                'Test Push Notification',
                'This device received a push from the Faralokun Vital Herbs dashboard.',
                url='/dashboard/notifications/',
            )
            if push_result['devices'] == 0:
                messages.warning(request,
                                 'No push devices subscribed to your account yet — click '
                                 '"Enable Notifications" on the dashboard first.')
            else:
                messages.success(request,
                                 f"Test push delivered to {push_result['sent']} of "
                                 f"{push_result['devices']} device(s).")
        return redirect('dashboard:site_settings')

    messages.info(request, 'Unknown test action.')
    return redirect('dashboard:site_settings')


# ── STAFF & ACCESS ────────────────────────────────────────────────────────────
# Deliberately separate from Django Admin's User management: this never
# touches is_staff/is_superuser, only the custom StaffAccess role/sections
# (see api/permissions.py and dashboard/models.py for why).
@owner_required
def staff_list(request):
    return render(request, 'dashboard/staff_list.html', {
        'active_nav': 'staff',
        'staff_members': StaffAccess.objects.select_related('user').all(),
        **_badge_counts(),
    })


@owner_required
def staff_add(request):
    from .forms import StaffCreateForm
    if request.method == 'POST':
        form = StaffCreateForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password1'],
                first_name=form.cleaned_data.get('first_name', ''),
                last_name=form.cleaned_data.get('last_name', ''),
                # Deliberately NOT is_staff/is_superuser -- dashboard access
                # is granted purely through the StaffAccess row below.
            )
            StaffAccess.objects.create(
                user=user,
                role=form.cleaned_data['role'],
                sections=form.cleaned_data.get('sections', []),
                is_active=True,
            )
            messages.success(request, f'Staff account created for {user.username}.')
            return redirect('dashboard:staff')
        else:
            messages.warning(request, 'Please correct the errors below.')
    else:
        form = StaffCreateForm()
    return render(request, 'dashboard/staff_form.html', {
        'active_nav': 'staff', 'form': form, 'is_edit': False,
        **_badge_counts(),
    })


@owner_required
def staff_edit(request, pk):
    from .forms import StaffEditForm
    access = get_object_or_404(StaffAccess.objects.select_related('user'), pk=pk)
    if request.method == 'POST':
        form = StaffEditForm(request.POST, instance=access)
        if form.is_valid():
            if access.user == request.user and not form.cleaned_data['is_active']:
                messages.error(request, "You can't revoke your own dashboard access.")
            else:
                form.save()
                new_password = form.cleaned_data.get('new_password')
                if new_password:
                    access.user.set_password(new_password)
                    access.user.save(update_fields=['password'])
                messages.success(request, f'Access updated for {access.user.username}.')
                return redirect('dashboard:staff')
        else:
            messages.warning(request, 'Please correct the errors below.')
    else:
        form = StaffEditForm(instance=access)
    return render(request, 'dashboard/staff_form.html', {
        'active_nav': 'staff', 'form': form, 'is_edit': True, 'staff_access': access,
        **_badge_counts(),
    })

# ── ACCOUNT & SECURITY ───────────────────────────────────────────────────────
def _other_active_sessions(user, exclude_session_key):
    """
    Django's default session backend doesn't index sessions by user, so
    finding "this user's other sessions" means decoding each stored
    session's data -- the standard, well-known approach for this (not
    custom crypto; SessionStore().decode() is Django's own signed/decoded
    session payload).
    """
    from django.contrib.sessions.models import Session
    from django.contrib.sessions.backends.db import SessionStore
    matches = []
    for session in Session.objects.filter(expire_date__gte=timezone.now()):
        if session.session_key == exclude_session_key:
            continue
        try:
            data = SessionStore().decode(session.session_data)
        except Exception:
            continue
        if str(data.get('_auth_user_id')) == str(user.pk):
            matches.append(session)
    return matches


@staff_required
def account_security(request):
    from django.contrib.auth.forms import PasswordChangeForm
    from django.contrib.auth import update_session_auth_hash
    user = request.user
    two_factor = getattr(user, 'two_factor', None)
    password_form = PasswordChangeForm(user=user)

    if request.method == 'POST' and request.POST.get('action') == 'change_password':
        password_form = PasswordChangeForm(user=user, data=request.POST)
        if password_form.is_valid():
            password_form.save()
            update_session_auth_hash(request, user)  # keep the current session logged in
            messages.success(request, 'Password changed successfully.')
            return redirect('dashboard:account_security')
        else:
            messages.warning(request, 'Please correct the errors below.')

    other_sessions = _other_active_sessions(user, request.session.session_key)

    return render(request, 'dashboard/account_security.html', {
        'active_nav': 'account_security',
        'password_form': password_form,
        'two_factor': two_factor,
        'other_session_count': len(other_sessions),
        **_badge_counts(),
    })


@staff_required
@require_POST
def logout_other_sessions(request):
    sessions = _other_active_sessions(request.user, request.session.session_key)
    for session in sessions:
        session.delete()
    messages.success(request, f'Signed out of {len(sessions)} other session(s).')
    return redirect('dashboard:account_security')


@staff_required
def two_factor_setup(request):
    user = request.user
    two_factor, _ = TwoFactorAuth.objects.get_or_create(user=user, defaults={'secret': two_factor_service.generate_secret()})

    if two_factor.is_enabled:
        messages.info(request, '2FA is already enabled on your account.')
        return redirect('dashboard:account_security')

    if request.method == 'POST':
        code = request.POST.get('code', '')
        if two_factor_service.verify_code(two_factor.secret, code):
            two_factor.is_enabled = True
            two_factor.confirmed_at = timezone.now()
            two_factor.save(update_fields=['is_enabled', 'confirmed_at', 'updated_at'])
            recovery_codes = two_factor.generate_recovery_codes()
            request.session['just_generated_recovery_codes'] = recovery_codes
            messages.success(request, '2FA enabled! Save your recovery codes somewhere safe — they will not be shown again.')
            return redirect('dashboard:two_factor_recovery_codes')
        messages.error(request, 'That code was incorrect. Scan the QR code again and try the current 6-digit code.')

    uri = two_factor_service.provisioning_uri(two_factor.secret, user.username)
    qr_data_uri = two_factor_service.qr_code_data_uri(uri)
    return render(request, 'dashboard/two_factor_setup.html', {
        'active_nav': 'account_security',
        'qr_data_uri': qr_data_uri, 'secret': two_factor.secret,
        **_badge_counts(),
    })


@staff_required
def two_factor_recovery_codes(request):
    """
    Shows recovery codes exactly once, immediately after generation --
    pulled from the session (set by two_factor_setup or
    two_factor_regenerate_codes) and cleared on this same view, so a
    refresh or revisit can never redisplay them.
    """
    codes = request.session.pop('just_generated_recovery_codes', None)
    if not codes:
        return redirect('dashboard:account_security')
    return render(request, 'dashboard/two_factor_recovery_codes.html', {
        'active_nav': 'account_security', 'codes': codes,
        **_badge_counts(),
    })


@staff_required
@require_POST
def two_factor_regenerate_codes(request):
    two_factor = getattr(request.user, 'two_factor', None)
    if not two_factor or not two_factor.is_enabled:
        messages.error(request, 'Enable 2FA first.')
        return redirect('dashboard:account_security')
    codes = two_factor.generate_recovery_codes()
    request.session['just_generated_recovery_codes'] = codes
    messages.success(request, 'New recovery codes generated — your old codes no longer work.')
    return redirect('dashboard:two_factor_recovery_codes')


@staff_required
@require_POST
def two_factor_disable(request):
    two_factor = getattr(request.user, 'two_factor', None)
    password = request.POST.get('password', '')
    if not request.user.check_password(password):
        messages.error(request, 'Incorrect password — 2FA was not disabled.')
        return redirect('dashboard:account_security')
    if two_factor:
        two_factor.delete()
    messages.success(request, '2FA has been disabled on your account.')
    return redirect('dashboard:account_security')


# ── PASSWORD RECOVERY (dashboard staff — separate from the patient portal's) ──
def password_reset_request(request):
    from django.contrib.auth.forms import PasswordResetForm
    from django.contrib.auth.tokens import default_token_generator
    from django.utils.http import urlsafe_base64_encode
    from django.utils.encoding import force_bytes
    from django.template.loader import render_to_string

    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            users = list(form.get_users(email))
            for user in users:
                if not has_dashboard_access(user):
                    continue  # don't leak whether a non-staff email exists
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)
                reset_url = request.build_absolute_uri(
                    reverse('dashboard:password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
                )
                site = SiteSettings.get()
                try:
                    from django.core.mail import send_mail
                    send_mail(
                        subject=f'Password reset — {site.site_name} Dashboard',
                        message=(
                            f'Someone requested a password reset for your {site.site_name} staff '
                            f'dashboard account.\n\nReset your password:\n{reset_url}\n\n'
                            f'This link expires soon and can only be used once. If you did not '
                            f'request this, you can safely ignore this email.'
                        ),
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user.email],
                        fail_silently=True,
                    )
                except Exception:
                    logger.exception(f'Password reset email failed for user {user.pk}')
            # Always show the same message, whether or not the email matched
            # a staff account -- don't leak which emails exist.
            messages.success(request, "If that email has staff dashboard access, we've sent a reset link.")
            return redirect('dashboard:login')
    else:
        form = PasswordResetForm()
    return render(request, 'dashboard/password_reset_request.html', {'form': form})


def password_reset_confirm(request, uidb64, token):
    from django.contrib.auth.forms import SetPasswordForm
    from django.contrib.auth.tokens import default_token_generator
    from django.utils.http import urlsafe_base64_decode
    from django.utils.encoding import force_str

    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    valid_link = user is not None and default_token_generator.check_token(user, token)

    if valid_link and request.method == 'POST':
        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Password reset — you can now log in.')
            return redirect('dashboard:login')
    elif valid_link:
        form = SetPasswordForm(user)
    else:
        form = None

    return render(request, 'dashboard/password_reset_confirm.html', {
        'form': form, 'valid_link': valid_link,
    })
