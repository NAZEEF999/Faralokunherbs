"""
Email notification service for Faralokun Vital Herbs.
Uses Django's email backend — configure Gmail SMTP in .env to activate.
Falls back to console printing if EMAIL_BACKEND is not set.
"""
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def send_appointment_confirmation(appointment):
    """Send confirmation email to patient after booking."""
    if not appointment.contact_email:
        return  # No email address — skip silently

    from .models import SiteSettings
    site = SiteSettings.get()

    subject = f'Appointment Received — {site.site_name}'
    context = {
        'site_name':       site.site_name,
        'tagline':         site.tagline or '',
        'patient_name':    appointment.contact_name,
        'service_name':    appointment.service_name or 'General Consultation',
        'appointment_date': str(appointment.appointment_date) if appointment.appointment_date else '',
        'preferred_time':  appointment.preferred_time or '',
        'phone':           appointment.contact_phone,
        'contact_phone':   site.contact_phone,
        'whatsapp_number': site.whatsapp_number,
        'address':         site.address,
        'notes':           appointment.notes or '',
    }

    html_body  = render_to_string('emails/appointment_confirmation.html', context)
    text_body  = (
        f"Salaam {appointment.contact_name},\n\n"
        f"Your appointment at {site.site_name} has been received.\n"
        f"Service: {context['service_name']}\n"
        f"Date: {context['appointment_date'] or 'To be confirmed'}\n"
        f"Time: {context['preferred_time'] or 'To be confirmed'}\n\n"
        f"We will call you at {appointment.contact_phone} to confirm.\n\n"
        f"WE CURE, ALLAH HEALS.\n{site.site_name}"
    )

    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[appointment.contact_email],
        )
        msg.attach_alternative(html_body, 'text/html')
        msg.send(fail_silently=False)
        logger.info(f'Confirmation email sent to {appointment.contact_email}')
    except Exception as e:
        logger.error(f'Email send failed: {e}')


def send_booking_notification_email(appointment):
    """
    Owner/staff-facing "new booking" alert email -- distinct from
    send_appointment_confirmation() above, which goes to the CUSTOMER.
    Always attempts to send when called (the ON/OFF toggle is checked by
    the caller, api.utils.notify_new_booking); only skips if no recipient
    email can be resolved at all.

    Returns True/False so the caller can log/report the outcome without
    this ever raising into the booking view.
    """
    from .models import SiteSettings
    site = SiteSettings.get()
    recipient = site.effective_booking_email
    if not recipient:
        logger.warning('Booking notification email skipped: no recipient email configured.')
        return False

    from django.urls import reverse
    subject = f'New Booking — {site.site_name}'
    context = {
        'site_name':        site.site_name,
        'customer_name':    appointment.contact_name,
        'customer_phone':   appointment.contact_phone,
        'customer_email':   appointment.contact_email or 'Not provided',
        'service_name':     appointment.service_name or 'General Consultation',
        'appointment_date': str(appointment.appointment_date) if appointment.appointment_date else 'To be confirmed',
        'preferred_time':   appointment.preferred_time or 'To be confirmed',
        'notes':            appointment.notes or '',
        'dashboard_url':    reverse('dashboard:appointment_detail', args=[appointment.pk]),
    }

    html_body = render_to_string('emails/booking_notification.html', context)
    text_body = (
        f"NEW {site.site_name.upper()} BOOKING\n\n"
        f"Customer: {context['customer_name']}\n"
        f"Phone: {context['customer_phone']}\n"
        f"Email: {context['customer_email']}\n"
        f"Service: {context['service_name']}\n"
        f"Date: {context['appointment_date']}\n"
        f"Time: {context['preferred_time']}\n"
        f"Notes: {context['notes'] or '—'}\n\n"
        f"This booking requires your attention — please review and confirm it in the "
        f"{site.site_name} dashboard."
    )

    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient],
        )
        msg.attach_alternative(html_body, 'text/html')
        msg.send(fail_silently=False)
        logger.info(f'Booking notification email sent to {recipient}')
        return True
    except Exception as e:
        logger.error(f'Booking notification email failed: {e}')
        return False


def send_appointment_status_update(appointment):
    """Notify patient when admin changes appointment status."""
    if not appointment.contact_email:
        return

    from .models import SiteSettings
    site = SiteSettings.get()

    STATUS_MESSAGES = {
        'confirmed': 'Your appointment has been CONFIRMED.',
        'cancelled': 'Your appointment has been cancelled. Please contact us to reschedule.',
        'completed': 'Thank you for visiting us. We hope you found healing and relief.',
    }

    msg_text = STATUS_MESSAGES.get(appointment.status)
    if not msg_text:
        return

    subject  = f'Appointment Update — {site.site_name}'
    body     = (
        f"Salaam {appointment.contact_name},\n\n"
        f"{msg_text}\n\n"
        f"Service: {appointment.service_name or 'General Consultation'}\n"
        f"Date: {appointment.appointment_date or 'N/A'}\n\n"
        f"Questions? Call: {site.contact_phone}\n\n"
        f"WE CURE, ALLAH HEALS.\n{site.site_name}"
    )

    try:
        from django.core.mail import send_mail
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL,
                  [appointment.contact_email], fail_silently=False)
    except Exception as e:
        logger.error(f'Status update email failed: {e}')


def _send_owner_email(recipient, subject, context, template_name, text_body_builder):
    """Shared send for owner-facing alert emails. Returns True on success."""
    if not recipient:
        logger.warning('Owner notification email skipped: no recipient configured. (%s)', subject)
        return False
    try:
        html_body = render_to_string(template_name, context)
        text_body = text_body_builder(context)
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient],
        )
        msg.attach_alternative(html_body, 'text/html')
        msg.send(fail_silently=False)
        logger.info('Owner notification email sent to %s (%s)', recipient, subject)
        return True
    except Exception as exc:
        logger.error(f'Owner notification email failed ({subject}): {exc}')
        return False


def send_inquiry_notification_email(inquiry):
    """Owner/staff-facing alert for a new contact enquiry. Returns True/False."""
    from .models import SiteSettings
    from django.urls import reverse
    site = SiteSettings.get()
    recipient = site.effective_notification_email
    subject = f'New {site.site_name} Contact Enquiry — {inquiry.name}'
    context = {
        'site_name':     site.site_name,
        'customer_name': inquiry.name,
        'customer_phone': inquiry.phone or 'Not provided',
        'customer_email': inquiry.email or 'Not provided',
        'message':       inquiry.message,
        'dashboard_url': reverse('dashboard:message_detail', args=[inquiry.pk]),
    }

    def text_builder(ctx):
        return (
            f"NEW {site.site_name.upper()} CONTACT ENQUIRY\n\n"
            f"From: {ctx['customer_name']}\n"
            f"Phone: {ctx['customer_phone']}\n"
            f"Email: {ctx['customer_email']}\n"
            f"Message: {ctx['message']}\n\n"
            f"Reply to this customer from the {site.site_name} dashboard."
        )

    return _send_owner_email(recipient, subject, context,
                             'emails/inquiry_notification.html', text_builder)


def send_product_enquiry_notification_email(inquiry):
    """Owner/staff-facing alert for a new product enquiry. Returns True/False."""
    from .models import SiteSettings
    from django.urls import reverse
    site = SiteSettings.get()
    recipient = site.effective_notification_email
    subject = f'New {site.site_name} Product Enquiry — {inquiry.name}'
    context = {
        'site_name':     site.site_name,
        'customer_name': inquiry.name,
        'customer_phone': inquiry.phone or 'Not provided',
        'customer_email': inquiry.email or 'Not provided',
        'product_name':  getattr(inquiry, 'product_name', '') or '',
        'quantity':      getattr(inquiry, 'quantity_display', '') or '',
        'message':       inquiry.message,
        'dashboard_url': reverse('dashboard:message_detail', args=[inquiry.pk]),
    }

    def text_builder(ctx):
        lines = [
            f"NEW {site.site_name.upper()} PRODUCT ENQUIRY",
            "",
            f"From: {ctx['customer_name']}",
            f"Phone: {ctx['customer_phone']}",
            f"Email: {ctx['customer_email']}",
        ]
        if ctx['product_name']:
            lines.append(f"Product: {ctx['product_name']}")
        if ctx['quantity']:
            lines.append(f"Quantity: {ctx['quantity']}")
        lines += ["", f"Message: {ctx['message']}", "",
                  f"Reply to this customer from the {site.site_name} dashboard."]
        return "\n".join(lines)

    return _send_owner_email(recipient, subject, context,
                             'emails/product_enquiry_notification.html', text_builder)


def send_order_notification_email(order):
    """Owner/staff-facing alert for a new product order. Returns True/False."""
    from .models import SiteSettings
    from django.urls import reverse
    site = SiteSettings.get()
    recipient = site.effective_notification_email
    subject = f'New {site.site_name} Order — {order.order_number}'
    context = {
        'site_name':     site.site_name,
        'order_number':  order.order_number,
        'customer_name': order.customer_name,
        'customer_phone': order.customer_phone,
        'customer_email': order.customer_email or 'Not provided',
        'delivery_address': order.delivery_address or '—',
        'notes':         order.notes or '',
        'items':         order.items.all(),
        'item_count':    order.item_count,
        'dashboard_url': reverse('dashboard:order_detail', args=[order.pk]),
    }

    def text_builder(ctx):
        lines = [f"NEW {site.site_name.upper()} ORDER — {ctx['order_number']}", "",
                 f"Customer: {ctx['customer_name']}",
                 f"Phone: {ctx['customer_phone']}",
                 f"Email: {ctx['customer_email']}",
                 "Items:",
                 *[f"  {i.quantity}x {i.product_name}" for i in order.items.all()],
                 f"Delivery: {ctx['delivery_address']}",
                 f"Customer notes: {ctx['notes'] or '—'}",
                 "",
                 f"Please review and confirm in the {site.site_name} dashboard."]
        return "\n".join(lines)

    return _send_owner_email(recipient, subject, context,
                             'emails/order_notification.html', text_builder)


def send_test_email(to_email):
    """
    'Send test email' action for the dashboard Site Settings page.
    Returns True/False and never raises into the view.
    """
    from .models import SiteSettings
    site = SiteSettings.get()
    body = (
        f"This is a test email from {site.site_name}.\n"
        f"It confirms that your email configuration (host, port, user, password, TLS) is working.\n"
        f"If you received this, notifications will reach this address.\n\n"
        f"Current recipient: {to_email or site.contact_email}\n"
        f"Date sent: {__import__('django.utils.timezone', fromlist=['now']).now().strftime('%Y-%m-%d %H:%M %Z')}"
    )
    try:
        from django.core.mail import send_mail
        send_mail(
            f'Test Notification — {site.site_name}',
            body,
            settings.DEFAULT_FROM_EMAIL,
            [to_email or site.contact_email],
            fail_silently=False,
        )
        logger.info('Test email sent to %s', to_email or site.contact_email)
        return True
    except Exception as exc:
        logger.error(f'Test email failed: {exc}')
        return False
