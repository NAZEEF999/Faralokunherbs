from .models import Notification, SiteSettings
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def create_notification(ntype, title, message, url=''):
    """Create a bell notification in the staff dashboard + push it to staff devices."""
    Notification.objects.create(
        type=ntype,
        title=title,
        message=message,
        url=url,
        is_read=False
    )
    # Every meaningful dashboard event (appointment/inquiry/order/subscriber)
    # is also pushed to subscribed staff devices. 'general' rows are
    # operational (e.g. "email failed") so they stay bell-only.
    if ntype != 'general':
        try:
            from . import push_service
            push_service.send_to_all_staff(title, message, url=url)
        except Exception:
            logger.exception('Push broadcast failed for notification: %s', title)


def get_whatsapp_url(number: str, message: str) -> str:
    clean = ''.join(c for c in number if c.isdigit())
    from urllib.parse import quote
    return f'https://wa.me/{clean}?text={quote(message)}'


def trigger_whatsapp_alert(message: str) -> str | None:
    try:
        settings = SiteSettings.get()
        if not settings.whatsapp_number:
            logger.warning('No WhatsApp number configured in SiteSettings — cannot build notification link.')
            return None
        return get_whatsapp_url(settings.whatsapp_number, message)
    except Exception:
        logger.exception('Failed to build WhatsApp notification link.')
        return None


def build_appointment_wa_message(appointment) -> str:
    try:
        site = SiteSettings.get()
        site_name = site.site_name
    except Exception:
        site_name = 'Faralokun Vital Herbs'
    # Deliberately excludes appointment.notes: WhatsApp is an external
    # channel outside the authorized staff dashboard, so no medical
    # notes/symptoms/history ever go into this message.
    return (
        f"New Appointment Request — {site_name}\n\n"
        f"Name: {appointment.contact_name}\n"
        f"Service: {appointment.service_name or 'General Consultation'}\n"
        f"Preferred Date: {appointment.appointment_date or 'To be confirmed'}\n"
        f"Preferred Time: {appointment.preferred_time or 'To be confirmed'}\n"
        f"Phone: {appointment.contact_phone}\n"
        f"Email: {appointment.contact_email or 'Not provided'}\n\n"
        f"Please review this appointment in the staff dashboard."
    )


def build_booking_whatsapp_business_message(appointment, site_name) -> str:
    """
    Message body for the AUTOMATIC WhatsApp Business API notification
    (api.whatsapp_service), sent server-to-server straight to the owner's
    configured business number -- a trusted internal channel, same trust
    level as the booking notification email, so (unlike the public wa.me
    link above) this one does include notes.
    """
    lines = [
        f"\U0001F514 New {site_name} Booking",
        "",
        f"Customer: {appointment.contact_name}",
        f"Phone: {appointment.contact_phone}",
    ]
    if appointment.contact_email:
        lines.append(f"Email: {appointment.contact_email}")
    lines += [
        "",
        f"Service: {appointment.service_name or 'General Consultation'}",
        f"Date: {appointment.appointment_date or 'To be confirmed'}",
        f"Time: {appointment.preferred_time or 'To be confirmed'}",
    ]
    if appointment.notes:
        lines += ["", "Notes:", appointment.notes]
    lines += ["", f"Please review the booking in the {site_name} dashboard."]
    return "\n".join(lines)


def notify_new_booking(appointment):
    """
    Fires the owner/staff-facing booking notifications: email and/or
    WhatsApp Business, each independently gated by its own ON/OFF toggle
    in Website Settings. The appointment itself is already saved by the
    time this runs -- notification outcome never affects that.

    Returns a small dict describing what happened, and files an in-dashboard
    Notification if a channel was enabled but failed to actually send, so
    a misconfiguration is visible in the product, not just server logs.
    """
    site = SiteSettings.get()
    result = {'email_attempted': False, 'email_sent': False,
              'whatsapp_attempted': False, 'whatsapp_sent': False, 'whatsapp_detail': ''}

    if site.email_notifications_enabled:
        result['email_attempted'] = True
        from .email_service import send_booking_notification_email
        try:
            result['email_sent'] = send_booking_notification_email(appointment)
        except Exception:
            logger.exception(f'Booking notification email raised for appointment {appointment.pk}')
        if not result['email_sent']:
            create_notification(
                'general', 'Booking email notification failed',
                f"Couldn't email the new-booking alert for {appointment.contact_name} — "
                f"check Website Settings > Booking Notifications and email configuration."
            )

    if site.whatsapp_notifications_enabled:
        result['whatsapp_attempted'] = True
        from . import whatsapp_service
        message = build_booking_whatsapp_business_message(appointment, site.site_name)
        sent, detail = whatsapp_service.send_business_whatsapp_message(
            site.effective_booking_whatsapp, message
        )
        result['whatsapp_sent'] = sent
        result['whatsapp_detail'] = detail
        if not sent:
            create_notification(
                'general', 'Booking WhatsApp notification failed',
                f"Couldn't send the automatic WhatsApp alert for {appointment.contact_name}'s "
                f"booking — {detail}"
            )

    return result


def build_order_wa_message(order) -> str:
    try:
        site = SiteSettings.get()
        site_name = site.site_name
    except Exception:
        site_name = 'Faralokun Vital Herbs'
    # Prices stay internal: this wa.me prefill goes to customers, so item
    # lines intentionally exclude amounts (pricing is shared personally).
    lines = [f'{item.quantity}x {item.product_name}' for item in order.items.all()]
    items_block = '\n'.join(lines) if lines else 'No items'
    return (
        f"New Order at {site_name}! ({order.order_number})\n"
        f"Customer: {order.customer_name}\n"
        f"Items:\n{items_block}\n"
        f"Phone: {order.customer_phone}\n"
        f"Email: {order.customer_email or 'Not provided'}"
    )


def build_cart_wa_message(cart, greeting='') -> str:
    """
    Customer-facing WhatsApp prefill built from the shopping cart.
    Strictly items + quantities — never prices (pricing is shared
    personally after an enquiry/order).
    """
    try:
        site = SiteSettings.get()
        site_name = site.site_name
    except Exception:
        site_name = 'Faralokun Vital Herbs'
    lines = [f'{item.quantity}x {item.product.title}' for item in cart.item_list]
    items_block = '\n'.join(lines) if lines else 'No items'
    return (
        f"Hello {site_name}! I would like to order the following:\n\n"
        f"{items_block}\n\n"
        "Please share pricing and delivery details."
    )


def build_cart_whatsapp_url(cart, greeting='') -> str | None:
    """wa.me link for the public WHATSAPP checkout path (no prices)."""
    try:
        site = SiteSettings.get()
        if not site.whatsapp_number:
            return None
        message = build_cart_wa_message(cart, greeting=greeting)
        return get_whatsapp_url(site.whatsapp_number, message)
    except Exception:
        logger.exception('Failed to build cart WhatsApp checkout link.')
        return None


def build_inquiry_wa_message(inquiry) -> str:
    try:
        site = SiteSettings.get()
        site_name = site.site_name
    except Exception:
        site_name = 'Faralokun Vital Herbs'
    return (
        f"New Inquiry at {site_name}!\n"
        f"From: {inquiry.name}\n"
        f"Phone: {inquiry.phone or 'Not provided'}\n"
        f"Email: {inquiry.email or 'Not provided'}\n"
        f"Message: {inquiry.message}"
    )


def build_product_enquiry_wa_message(inquiry) -> str:
    """
    WhatsApp message for a product enquiry (the customer-facing CTA is
    'Contact for Enquiry' -- no prices are ever included here).
    """
    try:
        site = SiteSettings.get()
        site_name = site.site_name
    except Exception:
        site_name = 'Faralokun Vital Herbs'
    return (
        f"New Product Enquiry at {site_name}!\n"
        f"From: {inquiry.name}\n"
        f"Phone: {inquiry.phone or 'Not provided'}\n"
        f"Email: {inquiry.email or 'Not provided'}\n"
        f"Message: {inquiry.message}"
    )


def _record_notification_failure(ntype, subject, reason):
    create_notification(
        'general', f'{subject} failed',
        f"Couldn't send the {subject.lower()} — {reason}"
    )


def notify_new_inquiry(inquiry):
    """
    Owner/staff-facing alerts for a contact inquiry: optional email and
    WhatsApp Business, independently gated. The inquiry is already saved --
    notification outcome never affects that.
    """
    site = SiteSettings.get()
    result = {'email_attempted': False, 'email_sent': False,
              'whatsapp_attempted': False, 'whatsapp_sent': False, 'whatsapp_detail': ''}

    if site.enquiry_email_notifications_enabled:
        result['email_attempted'] = True
        from .email_service import send_inquiry_notification_email
        try:
            result['email_sent'] = send_inquiry_notification_email(inquiry)
        except Exception:
            logger.exception(f'Inquiry notification email raised for inquiry {inquiry.pk}')
        if not result['email_sent']:
            _record_notification_failure(
                'general', 'Inquiry email notification', 'check Website Settings and email configuration.'
            )

    if site.notification_whatsapp_enabled:
        result['whatsapp_attempted'] = True
        from . import whatsapp_service
        sent, detail = whatsapp_service.send_business_whatsapp_message(
            site.effective_notification_whatsapp, build_inquiry_wa_message(inquiry)
        )
        result['whatsapp_sent'] = sent
        result['whatsapp_detail'] = detail
        if not sent:
            _record_notification_failure(
                'general', 'Inquiry WhatsApp notification', detail
            )
    return result


def notify_new_product_enquiry(inquiry):
    site = SiteSettings.get()
    result = {'email_attempted': False, 'email_sent': False,
              'whatsapp_attempted': False, 'whatsapp_sent': False, 'whatsapp_detail': ''}

    if site.enquiry_email_notifications_enabled:
        result['email_attempted'] = True
        from .email_service import send_product_enquiry_notification_email
        try:
            result['email_sent'] = send_product_enquiry_notification_email(inquiry)
        except Exception:
            logger.exception(f'Product enquiry notification email raised for inquiry {inquiry.pk}')
        if not result['email_sent']:
            _record_notification_failure(
                'general', 'Product enquiry email notification', 'check Website Settings and email configuration.'
            )

    if site.notification_whatsapp_enabled:
        result['whatsapp_attempted'] = True
        from . import whatsapp_service
        sent, detail = whatsapp_service.send_business_whatsapp_message(
            site.effective_notification_whatsapp, build_product_enquiry_wa_message(inquiry)
        )
        result['whatsapp_sent'] = sent
        result['whatsapp_detail'] = detail
        if not sent:
            _record_notification_failure(
                'general', 'Product enquiry WhatsApp notification', detail
            )
    return result


def notify_new_order(order):
    """
    Owner/staff-facing alerts for a new product order: optional email and
    WhatsApp Business, independently gated. The order is already saved.
    """
    site = SiteSettings.get()
    result = {'email_attempted': False, 'email_sent': False,
              'whatsapp_attempted': False, 'whatsapp_sent': False, 'whatsapp_detail': ''}

    if site.order_email_notifications_enabled:
        result['email_attempted'] = True
        from .email_service import send_order_notification_email
        try:
            result['email_sent'] = send_order_notification_email(order)
        except Exception:
            logger.exception(f'Order notification email raised for order {order.pk}')
        if not result['email_sent']:
            _record_notification_failure(
                'general', 'Order email notification', 'check Website Settings and email configuration.'
            )

    if site.notification_whatsapp_enabled:
        result['whatsapp_attempted'] = True
        from . import whatsapp_service
        sent, detail = whatsapp_service.send_business_whatsapp_message(
            site.effective_notification_whatsapp, build_order_wa_message(order)
        )
        result['whatsapp_sent'] = sent
        result['whatsapp_detail'] = detail
        if not sent:
            _record_notification_failure(
                'general', 'Order WhatsApp notification', detail
            )
    return result


def send_admin_email(subject: str, message: str) -> None:
    """Send email notification to admin."""
    try:
        from django.core.mail import send_mail
        from django.conf import settings
        admin_email = SiteSettings.get().contact_email
        if not admin_email:
            return
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[admin_email],
            fail_silently=False,
        )
    except Exception:
        logger.exception(f'Failed to send admin notification email: {subject}')


def notify_admin_appointment(appointment) -> None:
    """Email admin about new appointment."""
    send_admin_email(
        subject=f'New Appointment — {appointment.contact_name}',
        message=build_appointment_wa_message(appointment)
    )


def notify_admin_order(order) -> None:
    """Email admin about new product order."""
    send_admin_email(
        subject=f'New Product Order — {order.customer_name}',
        message=build_order_wa_message(order)
    )


def notify_admin_inquiry(inquiry) -> None:
    """Email admin about new inquiry."""
    send_admin_email(
        subject=f'New Inquiry — {inquiry.name}',
        message=build_inquiry_wa_message(inquiry)
    )



    # ── UNFOLD CALLBACKS ──────────────────────────────────────────────────────────

def appointment_badge(request):
    from .models import Appointment
    count = Appointment.objects.filter(status='pending').count()
    return str(count) if count > 0 else None


def inquiry_badge(request):
    from .models import Inquiry
    count = Inquiry.objects.filter(is_read=False).count()
    return str(count) if count > 0 else None


def notification_badge(request):
    from .models import Notification
    count = Notification.objects.filter(is_read=False).count()
    return str(count) if count > 0 else None


def order_badge(request):
    from .models import Order
    count = Order.objects.filter(status='pending').count()
    return str(count) if count > 0 else None


def environment_callback(request):
    if settings.DEBUG:
        return "Development"
    return "Production"


def dashboard_callback(request, context):
    from django.urls import reverse
    from .models import Appointment, Inquiry, Notification, Service, Product, Order
    context.update({
        "pending_appointments": Appointment.objects.filter(status='pending').count(),
        "unread_inquiries":     Inquiry.objects.filter(is_read=False).count(),
        "pending_orders":       Order.objects.filter(status='pending').count(),
        "unread_notifications": Notification.objects.filter(is_read=False).count(),
        "total_services":       Service.objects.filter(active=True).count(),
        "total_products":       Product.objects.filter(active=True).count(),
        "recent_appointments":  Appointment.objects.select_related('service').order_by('-created_at')[:6],
        "recent_inquiries":     Inquiry.objects.order_by('-created_at')[:5],
        # This admin homepage is an internal/emergency fallback -- its own
        # quick actions should route staff back to the real staff
        # interface (/dashboard/) rather than deeper into admin.
        # "Add Appointment" has no dashboard equivalent: appointments are
        # only created through the public booking flow by design, so this
        # points at the appointments list instead of a nonexistent create route.
        "quick_actions": [
            ("View Appointments", reverse('dashboard:appointments'), "calendar_add_on"),
            ("Add Service", reverse('dashboard:service_add'), "add_circle"),
            ("Add Product", reverse('dashboard:product_add'), "eco"),
            ("Write Blog Post", reverse('dashboard:blog_add'), "edit_note"),
            ("Site Settings", reverse('dashboard:site_settings'), "settings"),
        ],
    })
    return context