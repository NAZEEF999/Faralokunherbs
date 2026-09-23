from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import PatientProfile


@admin.register(PatientProfile)
class PatientProfileAdmin(ModelAdmin):
    list_display = ['full_name', 'user', 'phone', 'created_at']
    search_fields = [
        'user__first_name',
        'user__last_name',
        'user__email',
        'phone',
    ]
    readonly_fields = ['created_at', 'updated_at']