"""
Web Push (VAPID) notification service for the Faralokun Vital Herbs staff dashboard.

Server-side only. The VAPID private key lives in settings/env and never
reaches the browser; the dashboard JS only receives VAPID_PUBLIC_KEY to
create a PushSubscription, and registers that subscription with Django.

Delivery is best-effort: a failing/revoked device is dropped automatically
(following the Web Push spec's 410/404 contract) so stale subscriptions do
not pile up and never break a request.
"""
import json
import logging

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

from .models import PushSubscription


def is_configured():
    return bool(settings.VAPID_PUBLIC_KEY and settings.VAPID_PRIVATE_KEY)


def subscription_count():
    return PushSubscription.objects.count()


def _vapid_claims():
    subject = settings.VAPID_CLAIMS_EMAIL or settings.ADMIN_EMAIL
    claims = {'aud': 'https://fcm.googleapis.com'}
    if subject:
        if '@' in subject:
            claims['sub'] = f'mailto:{subject}'
        elif subject.startswith('http://') or subject.startswith('https://'):
            claims['sub'] = subject
    return claims


def build_push_payload(title, message, url='', icon=None, badge=None, sound='default'):
    """
    Payload sent to the service worker. The service worker renders the
    notification (so it works when the dashboard tab is closed); sound is
    handled in the foreground by dashboard-notify.js, which reads the user's
    saved preference -- Web Notifications cannot reliably autoplay customs
    audio in the background, so we rely on the OS sound + vibration there.
    """
    return {
        'title': title[:200],
        'message': message[:500],
        'url': url,
        'icon': icon or '/static/img/fv-mark.png',
        'badge': badge or '/static/img/fv-mark.png',
        'sound': sound,
        'timestamp': None,
    }


def send_to_subscription(subscription, title, message, url='', icon=None, badge=None, sound='default'):
    """
    Deliver one push to a single PushSubscription. Returns (sent, detail).
    Drops the subscription when the push server reports it is gone.
    """
    if not is_configured():
        detail = ('VAPID keys are not configured (VAPID_PUBLIC_KEY / VAPID_PRIVATE_KEY / '
                  'VAPID_CLAIMS_EMAIL in .env). Push notifications will not be delivered until set.')
        return False, detail

    from pywebpush import WebPushException, webpush

    payload = json.dumps(build_push_payload(title, message, url, icon, badge, sound))
    try:
        webpush(
            subscription_info={
                'endpoint': subscription.endpoint,
                'keys': {'p256dh': subscription.p256dh, 'auth': subscription.auth},
            },
            data=payload,
            vapid_private_key=settings.VAPID_PRIVATE_KEY,
            vapid_claims=_vapid_claims(),
            timeout=8,
        )
        subscription.last_used_at = timezone.now()
        subscription.save()
        return True, 'sent'
    except WebPushException as exc:
        # 404/410 => endpoint no longer valid; drop the stale row.
        try:
            status = getattr(exc.response, 'status_code', None)
        except Exception:
            status = None
        if status in (404, 410):
            subscription.delete()
            return False, 'subscription removed (device unsubscribed)'
        logger.warning('Web push delivery failed (status=%s): %s', status, exc)
        return False, 'delivery failed'
    except Exception as exc:  # timeout / network
        logger.warning('Web push exception for %s…: %s', subscription.endpoint[:60], exc)
        return False, 'delivery failed'


def send_to_user(user, title, message, url='', icon=None, badge=None, sound='default'):
    """
    Send a push to every device the given user has subscribed. Returns a
    small summary dict {configured, devices, sent, failed}.
    """
    subs = list(user.push_subscriptions.all())
    result = {'configured': is_configured(), 'devices': len(subs), 'sent': 0, 'failed': 0}
    for sub in subs:
        ok, _ = send_to_subscription(sub, title, message, url, icon, badge, sound)
        if ok:
            result['sent'] += 1
        else:
            result['failed'] += 1
    return result


def send_to_all_staff(title, message, url='', icon=None, badge=None, sound='default'):
    """
    Broadcast to every subscribed dashboard device (all staff users).
    """
    from django.contrib.auth.models import User
    users = User.objects.filter(push_subscriptions__isnull=False).distinct()
    result = {'configured': is_configured(), 'devices': 0, 'sent': 0, 'failed': 0}
    for user in users:
        r = send_to_user(user, title, message, url, icon, badge, sound)
        result['devices'] += r['devices']
        result['sent'] += r['sent']
        result['failed'] += r['failed']
    return result