"""
Generate a VAPID key pair for Web Push and print it in .env form.

    python manage.py generate_vapid_keys

Emits the same format as `npx web-push generate-vapid-keys`:
  * VAPID_PUBLIC_KEY  -- base64url of the 65-byte uncompressed P-256 point
  * VAPID_PRIVATE_KEY -- base64url of the 32-byte big-endian scalar

Copy the two lines into your production .env (with a matching
VAPID_CLAIMS_EMAIL). Keys are printed once and never stored anywhere.
"""
from base64 import urlsafe_b64encode

from cryptography.hazmat.primitives.asymmetric import ec
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Generate a VAPID public/private key pair for Web Push (Web Push API).'

    def handle(self, *args, **options):
        private_key = ec.generate_private_key(ec.SECP256R1())

        raw_private = private_key.private_numbers().private_value.to_bytes(32, 'big')

        public_numbers = private_key.public_key().public_numbers()
        raw_public_point = bytes([0x04]) + public_numbers.x.to_bytes(32, 'big') + public_numbers.y.to_bytes(32, 'big')

        def b64url(data):
            return urlsafe_b64encode(data).rstrip(b'=').decode('ascii')

        self.stdout.write(self.style.SUCCESS(
            '\nVAPID key pair generated for Web Push.\n'
            'Add these two lines (plus a VAPID_CLAIMS_EMAIL) to your .env, then '
            'restart the server:\n\n'
            f'  VAPID_PUBLIC_KEY={b64url(raw_public_point)}\n'
            f'  VAPID_PRIVATE_KEY={b64url(raw_private)}\n'
            f'  VAPID_CLAIMS_EMAIL=you@phara.ng\n\n'
        ))