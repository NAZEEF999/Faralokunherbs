from django.db import models
from django.contrib.auth.models import User


class StaffAccess(models.Model):
    """
    Custom-dashboard permissions for a staff member — deliberately a
    separate system from Django's is_staff/is_superuser, which control
    Django Admin (/admin/) access.

    Granting someone a StaffAccess row (even role='owner', full access)
    NEVER touches is_staff or is_superuser on their User — so dashboard
    staff created here can never log into /admin/ unless a developer
    explicitly makes them a Django staff/superuser separately (see
    api.permissions for the access rules this enforces).
    """
    ROLE_CHOICES = [
        ('owner',                'Owner (Full Access)'),
        ('product_manager',      'Product Manager'),
        ('content_manager',      'Content Manager'),
        ('order_manager',        'Order Manager'),
        ('appointment_manager',  'Appointment Manager'),
        ('custom',               'Custom'),
    ]

    # Section keys referenced by api.permissions and the @section_required
    # decorator on dashboard views. Keep this list and ROLE_SECTION_DEFAULTS
    # in sync with the sections actually checked in dashboard/views.py.
    SECTION_CHOICES = [
        ('products',     'Products, Categories, Inventory, Promotions'),
        ('orders',       'Orders, Customers'),
        ('appointments', 'Appointments / Bookings'),
        ('content',      'Services, Blog, Health Library, Testimonials'),
        ('messages',     'Messages, Subscribers'),
        ('settings',     'Website Settings'),
        ('staff',        'Staff & Access'),
    ]

    ROLE_SECTION_DEFAULTS = {
        'owner':               ['products', 'orders', 'appointments', 'content', 'messages', 'settings', 'staff'],
        'product_manager':     ['products'],
        'content_manager':     ['content'],
        'order_manager':       ['orders'],
        'appointment_manager': ['appointments'],
        'custom':              [],
    }

    user       = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_access')
    role       = models.CharField(max_length=30, choices=ROLE_CHOICES, default='custom')
    sections   = models.JSONField(
        default=list, blank=True,
        help_text='Dashboard sections this user can access. Auto-filled from Role unless Role is Custom.'
    )
    is_active  = models.BooleanField(
        default=True, help_text='Turn off to revoke dashboard access instantly without deleting the account.')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Staff Access'
        verbose_name_plural = 'Staff Access'
        ordering = ['user__username']

    def __str__(self):
        return f'{self.user.get_username()} ({self.get_role_display()})'

    def save(self, *args, **kwargs):
        if self.role != 'custom':
            self.sections = list(self.ROLE_SECTION_DEFAULTS.get(self.role, []))
        super().save(*args, **kwargs)

    def has_section(self, section):
        return self.is_active and section in (self.sections or [])


class TwoFactorAuth(models.Model):
    """
    TOTP-based two-factor authentication for dashboard staff accounts.
    Uses the pyotp library (RFC 6238 -- the same standard Google
    Authenticator, Microsoft Authenticator, and Authy all implement) --
    never custom cryptography.

    The TOTP secret is stored as-is (standard practice for TOTP --
    django-otp's own TOTPDevice does the same; it relies on database-level
    access control, same trust boundary as every other credential in this
    project). Recovery codes are the sensitive one-time secrets and ARE
    hashed with Django's own password hasher, shown to the user exactly
    once at generation time and never retrievable again afterward.
    """
    user           = models.OneToOneField(User, on_delete=models.CASCADE, related_name='two_factor')
    secret         = models.CharField(max_length=64)
    is_enabled     = models.BooleanField(default=False)
    confirmed_at   = models.DateTimeField(null=True, blank=True)
    recovery_codes = models.JSONField(default=list, blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'2FA for {self.user.get_username()} ({"enabled" if self.is_enabled else "not enabled"})'

    def generate_recovery_codes(self, count=8):
        """
        Generates fresh plaintext codes, stores only their hashes, and
        returns the PLAINTEXT list once. Callers must show these to the
        user immediately -- they can never be retrieved again afterward,
        only regenerated (which invalidates the old set).
        """
        import secrets
        from django.contrib.auth.hashers import make_password
        plaintext_codes = [f'{secrets.token_hex(2)}-{secrets.token_hex(2)}'.upper() for _ in range(count)]
        self.recovery_codes = [make_password(code) for code in plaintext_codes]
        self.save(update_fields=['recovery_codes', 'updated_at'])
        return plaintext_codes

    def verify_and_consume_recovery_code(self, code):
        """Each recovery code works once -- a successful match removes it."""
        from django.contrib.auth.hashers import check_password
        code = (code or '').strip().upper()
        for hashed in self.recovery_codes:
            if check_password(code, hashed):
                self.recovery_codes = [h for h in self.recovery_codes if h != hashed]
                self.save(update_fields=['recovery_codes', 'updated_at'])
                return True
        return False
