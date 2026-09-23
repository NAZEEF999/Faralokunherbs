from django.db import models
from django.contrib.auth.models import User


class PatientProfile(models.Model):
    """Extended profile for logged-in patients."""
    user       = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    phone      = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address    = models.TextField(blank=True)
    medical_notes = models.TextField(blank=True, help_text='Visible to staff and admin only')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user.get_full_name() or self.user.username} — Patient'

    @property
    def full_name(self):
        return self.user.get_full_name() or self.user.username

    @property
    def appointments(self):
        """
        All appointments for this patient: ones explicitly linked via the
        FK (set when they book while logged in), plus any older/guest
        bookings made with the same email before they had an account.
        """
        from django.db.models import Q
        from api.models import Appointment
        return Appointment.objects.filter(
            Q(patient=self) | Q(patient__isnull=True, contact_email=self.user.email)
        ).distinct().order_by('-created_at')
