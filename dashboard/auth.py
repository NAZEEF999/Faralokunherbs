from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse

from api.permissions import has_dashboard_access, has_dashboard_section, is_staff_owner


def staff_required(view_func):
    """
    Protects every /dashboard/ route with the real access rule (see
    api.permissions): a Django superuser, or a user with an active
    StaffAccess row. Ordinary patients (even logged in via the patient
    portal) and plain is_staff-only accounts with no StaffAccess are
    bounced out -- enforced here on the backend, not just a hidden link.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"{reverse('dashboard:login')}?next={request.path}")
        if not has_dashboard_access(request.user):
            messages.error(request, "You don't have access to the staff dashboard.")
            return redirect('api:home')
        return view_func(request, *args, **kwargs)
    return wrapper


def owner_required(view_func):
    """
    Protects Staff & Access management specifically -- granting/revoking
    other people's dashboard access is more sensitive than any single
    content section, so it needs the 'staff' section (or superuser), not
    just general dashboard access.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"{reverse('dashboard:login')}?next={request.path}")
        if not is_staff_owner(request.user):
            messages.error(request, "You don't have access to Staff & Access management.")
            return redirect('dashboard:overview')
        return view_func(request, *args, **kwargs)
    return wrapper


def section_required(section):
    """
    Protects a specific dashboard section (e.g. 'products', 'orders').
    Stacks on top of the general access rule in staff_required: a user
    can be a valid dashboard user (some StaffAccess row) but still be
    denied a section they weren't granted -- e.g. a Product Manager
    hitting /dashboard/orders/.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(f"{reverse('dashboard:login')}?next={request.path}")
            if not has_dashboard_section(request.user, section):
                messages.error(request, "You don't have access to that area of the dashboard.")
                return redirect('dashboard:overview')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
