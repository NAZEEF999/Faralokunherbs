"""
WhatsApp Business Platform (Cloud API) integration for automatic, real
booking notifications to the business owner/staff.

This is deliberately separate from the wa.me deep-link helpers in
api/utils.py (trigger_whatsapp_alert / build_*_wa_message), which only
open WhatsApp with a pre-filled message for a HUMAN to send manually.
This module calls Meta's Graph API to send a message server-to-server,
with no human action required -- that distinction matters: a wa.me link
is not "automatic," and this codebase never claims it is.

Configuration (server-side environment variables only -- never stored in
the database, never rendered into HTML/JS, never exposed to the dashboard
UI or the browser):

    WHATSAPP_BUSINESS_API_TOKEN        -- permanent/system-user access token
    WHATSAPP_BUSINESS_PHONE_NUMBER_ID  -- the sending number's Phone Number ID

Both come from environment variables via core/settings.py. If either is
missing, send_business_whatsapp_message() returns a clear failure instead
of pretending to have sent anything -- callers must never report success
to the owner unless Meta's API actually accepted the message.
"""
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT_SECONDS = 10


def is_configured():
    """True only when both required credentials are present."""
    return bool(settings.WHATSAPP_BUSINESS_API_TOKEN and settings.WHATSAPP_BUSINESS_PHONE_NUMBER_ID)


def send_business_whatsapp_message(to_number, message_text):
    """
    Sends a WhatsApp text message via the WhatsApp Business Cloud API.

    Returns (success: bool, detail: str). Never raises -- callers (booking
    views) must be able to save a booking and respond to the customer
    regardless of notification outcome, so every failure mode here is
    caught and reported as a return value, not thrown.
    """
    if not to_number:
        return False, 'No booking WhatsApp number is configured in Website Settings.'

    if not is_configured():
        logger.warning(
            'WhatsApp Business notification skipped: WHATSAPP_BUSINESS_API_TOKEN and/or '
            'WHATSAPP_BUSINESS_PHONE_NUMBER_ID are not set in the server environment. '
            'Set both to enable automatic WhatsApp booking alerts -- until then, '
            'WhatsApp notifications will not be sent even if enabled in Website Settings.'
        )
        return False, 'WhatsApp Business API is not configured on the server.'

    digits_only = ''.join(c for c in to_number if c.isdigit())
    url = (f'https://graph.facebook.com/{settings.WHATSAPP_API_VERSION}/'
           f'{settings.WHATSAPP_BUSINESS_PHONE_NUMBER_ID}/messages')
    headers = {
        'Authorization': f'Bearer {settings.WHATSAPP_BUSINESS_API_TOKEN}',
        'Content-Type': 'application/json',
    }
    payload = {
        'messaging_product': 'whatsapp',
        'to': digits_only,
        'type': 'text',
        'text': {'body': message_text, 'preview_url': False},
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=REQUEST_TIMEOUT_SECONDS)
    except requests.RequestException as e:
        logger.error(f'WhatsApp Business API request failed: {e}')
        return False, 'Could not reach the WhatsApp Business API.'

    if response.status_code == 200:
        logger.info(f'WhatsApp Business notification sent to ...{digits_only[-4:]}')
        return True, 'Sent.'

    # Never include the request payload or auth header in logs -- just Meta's
    # own error response, which is useful for diagnosing config problems
    # (bad token, unverified recipient in sandbox mode, etc.) without ever
    # printing the token itself.
    logger.error(f'WhatsApp Business API returned {response.status_code}: {response.text[:300]}')
    return False, f'WhatsApp Business API returned an error (status {response.status_code}).'
