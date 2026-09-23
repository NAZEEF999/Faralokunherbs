from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import PatientRegisterForm, PatientLoginForm, PatientProfileForm
from .models import PatientProfile
from api.models import Appointment, SiteSettings
import logging

logger = logging.getLogger(__name__)


# ── REGISTER ──────────────────────────────────────────────────────────────────
def register(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        form = PatientRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome, {user.first_name}! Your account has been created.')
            return redirect('accounts:dashboard')
    else:
        form = PatientRegisterForm()

    return render(request, 'accounts/register.html', {'form': form, 'page_title': f'Create Account | {SiteSettings.get().site_name}'})


# ── LOGIN ─────────────────────────────────────────────────────────────────────
def patient_login(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        form = PatientLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.GET.get('next', '')
            if not (next_url and url_has_allowed_host_and_scheme(
                    url=next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure())):
                next_url = 'accounts:dashboard'
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            return redirect(next_url)
    else:
        form = PatientLoginForm(request)

    return render(request, 'accounts/login.html', {'form': form, 'page_title': f'Patient Login | {SiteSettings.get().site_name}'})


# ── LOGOUT ────────────────────────────────────────────────────────────────────
def patient_logout(request):
    logout(request)
    messages.success(request, 'You have been signed out.')
    return redirect('api:home')


# ── DASHBOARD ─────────────────────────────────────────────────────────────────
@login_required(login_url='/portal/login/')
def dashboard(request):
    profile, _ = PatientProfile.objects.get_or_create(user=request.user)
    appointments = profile.appointments

    upcoming  = appointments.filter(status__in=['pending', 'confirmed'])
    completed = appointments.filter(status='completed')
    cancelled = appointments.filter(status='cancelled')

    return render(request, 'accounts/dashboard.html', {
        'profile':    profile,
        'upcoming':   upcoming[:5],
        'completed':  completed[:5],
        'cancelled':  cancelled[:3],
        'total':      appointments.count(),
        'upcoming_count':  upcoming.count(),
        'completed_count': completed.count(),
        'page_title': f'My Dashboard | {SiteSettings.get().site_name}',
    })


# ── APPOINTMENTS ──────────────────────────────────────────────────────────────
@login_required(login_url='/portal/login/')
def my_appointments(request):
    profile, _ = PatientProfile.objects.get_or_create(user=request.user)
    status = request.GET.get('status', '')
    appointments = profile.appointments
    if status:
        appointments = appointments.filter(status=status)

    STATUS_TABS = [
        ('', 'All', '#A0B5A3'),
        ('pending',   'Pending',   '#C49A3C'),
        ('confirmed', 'Confirmed', '#3A7D44'),
        ('completed', 'Completed', '#A0B5A3'),
        ('cancelled', 'Cancelled', '#f87171'),
    ]
    return render(request, 'accounts/appointments.html', {
        'profile':       profile,
        'appointments':  appointments,
        'active_status': status,
        'status_tabs':   STATUS_TABS,
        'page_title': f'My Appointments | {SiteSettings.get().site_name}',
    })


# ── PROFILE EDIT ──────────────────────────────────────────────────────────────
@login_required(login_url='/portal/login/')
def edit_profile(request):
    profile, _ = PatientProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = PatientProfileForm(request.POST, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            request.user.first_name = form.cleaned_data['first_name']
            request.user.last_name  = form.cleaned_data['last_name']
            request.user.save()
            profile.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('accounts:dashboard')
    else:
        form = PatientProfileForm(instance=profile)

    return render(request, 'accounts/profile.html', {
        'form': form, 'profile': profile,
        'page_title': f'My Profile | {SiteSettings.get().site_name}',
    })


# ── APPOINTMENT RECEIPT PDF ───────────────────────────────────────────────────
@login_required(login_url='/portal/login/')
def appointment_receipt_pdf(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk, contact_email=request.user.email)
    site = SiteSettings.get()

    html = render(request, 'pdf/appointment_receipt.html', {
        'appointment': appointment,
        'site': site,
        'now': timezone.now(),
    }).content

    try:
        from xhtml2pdf import pisa
        from io import BytesIO
        pdf_buffer = BytesIO()
        pisa.CreatePDF(html.decode('utf-8'), dest=pdf_buffer)
        pdf_buffer.seek(0)
        response = HttpResponse(pdf_buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'filename="appointment_{pk}.pdf"'
        return response
    except Exception as e:
        logger.exception(f'Appointment receipt PDF generation failed for appointment {pk}')
        messages.error(request, 'We could not generate your receipt right now. Please try again shortly.')
        return redirect('accounts:my_appointments')
