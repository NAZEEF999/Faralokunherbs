"""
TOTP (RFC 6238) helpers for dashboard 2FA -- thin wrappers around pyotp
and qrcode. No custom cryptography lives here; this module only handles
secret generation, provisioning-URI/QR-code building for the setup
screen, and code verification.
"""
import base64
import io

import pyotp
import qrcode
from django.conf import settings


def generate_secret():
    """A fresh random base32 TOTP secret (pyotp uses RFC 4648 base32, 160 bits)."""
    return pyotp.random_base32()


def provisioning_uri(secret, username):
    """
    The otpauth:// URI authenticator apps scan/import. Issuer name comes
    from Website Settings' site name so it shows correctly in the app
    even when a custom site name is configured.
    """
    from api.models import SiteSettings
    issuer = SiteSettings.get().site_name or 'Dashboard'
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=username, issuer_name=issuer)


def qr_code_data_uri(uri):
    """Renders the provisioning URI as a PNG QR code, inlined as a data: URI
    -- no external QR-code API call, so the secret never leaves the server."""
    img = qrcode.make(uri, border=2)
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    encoded = base64.b64encode(buffer.getvalue()).decode('ascii')
    return f'data:image/png;base64,{encoded}'


def verify_code(secret, code):
    """
    Verifies a 6-digit TOTP code, allowing 1 window (30s) of clock drift
    on either side -- standard, forgiving-but-still-tight tolerance.
    """
    if not code:
        return False
    code = code.strip().replace(' ', '')
    if not code.isdigit():
        return False
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)
