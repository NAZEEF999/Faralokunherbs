from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import StaffAccess, TwoFactorAuth


@admin.register(StaffAccess)
class StaffAccessAdmin(ModelAdmin):
    """
    Technical/emergency management only -- normal staff management happens
    in the custom dashboard's Staff & Access section
    (dashboard:staff / dashboard:staff_add / dashboard:staff_edit), which
    is what the business owner actually uses day to day.
    """
    list_display  = ['user', 'role', 'is_active', 'created_at']
    list_filter   = ['role', 'is_active']
    search_fields = ['user__username', 'user__email']
    autocomplete_fields = ['user']


@admin.register(TwoFactorAuth)
class TwoFactorAuthAdmin(ModelAdmin):
    """
    Emergency escape hatch: if a staff member loses both their
    authenticator device AND their recovery codes, a developer/superuser
    can delete this row here to reset 2FA on their account -- there is no
    other way back in otherwise. Recovery codes are hashed and the secret
    is intentionally not editable from here.
    """
    list_display    = ['user', 'is_enabled', 'confirmed_at']
    list_filter     = ['is_enabled']
    search_fields   = ['user__username', 'user__email']
    readonly_fields = ['secret', 'recovery_codes', 'created_at', 'updated_at']
    autocomplete_fields = ['user']
