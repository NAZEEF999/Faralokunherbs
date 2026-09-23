"""
Dashboard access rules -- deliberately independent of Django's
is_staff/is_superuser, which gate Django Admin (/admin/) instead.

    Developer / superuser  -> Django Admin: yes.  Dashboard: yes (full).
    Owner / staff (StaffAccess row, is_active=True)
                            -> Django Admin: no (unless separately made
                               is_staff by a developer). Dashboard: yes,
                               scoped to their granted sections.
    Everyone else           -> neither.

is_staff alone (with no StaffAccess row and not a superuser) grants NO
dashboard access -- that's the whole point of this split. Living here
(not in dashboard/auth.py) lets both the `api` and `dashboard` apps use
the same rules without a lower-level app importing a higher-level one.
"""


def has_dashboard_access(user):
    if not user or not user.is_authenticated or not user.is_active:
        return False
    if user.is_superuser:
        return True
    access = getattr(user, 'staff_access', None)
    return bool(access and access.is_active)


def has_dashboard_section(user, section):
    """True if the user can access a specific dashboard section."""
    if not has_dashboard_access(user):
        return False
    if user.is_superuser:
        return True
    access = getattr(user, 'staff_access', None)
    return bool(access and access.has_section(section))


def dashboard_sections(user):
    """All section keys the user can access (for nav rendering)."""
    if not user or not user.is_authenticated:
        return []
    if user.is_superuser:
        from dashboard.models import StaffAccess
        return [key for key, _ in StaffAccess.SECTION_CHOICES]
    access = getattr(user, 'staff_access', None)
    if access and access.is_active:
        return list(access.sections or [])
    return []


def is_staff_owner(user):
    """
    True for users allowed to manage OTHER staff accounts: superusers, or
    anyone with the 'staff' section (role='owner' gets this by default).
    Kept as its own check since granting staff-management access is more
    sensitive than any single content section.
    """
    return has_dashboard_section(user, 'staff')
