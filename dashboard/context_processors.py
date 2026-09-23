from api.permissions import has_dashboard_access, dashboard_sections, is_staff_owner


def dashboard_nav(request):
    """
    Available on every template (registered globally like api's
    site_settings processor) so dashboard/base_dashboard.html can hide
    nav links for sections the logged-in user wasn't granted, without
    threading this through every single dashboard view. The actual
    enforcement is still server-side in dashboard.auth -- this is just
    UI, so staff aren't shown links that would 403 anyway.
    """
    if not request.user.is_authenticated or not has_dashboard_access(request.user):
        return {}
    return {
        'my_dashboard_sections': dashboard_sections(request.user),
        'can_manage_staff': is_staff_owner(request.user),
    }
