from .models import SiteSettings, Notification
from .cart import get_cart
from .permissions import has_dashboard_access


def site_settings(request):
    site = SiteSettings.get()
    unread_notifications = 0

    if request.user.is_authenticated and has_dashboard_access(request.user):
        unread_notifications = Notification.objects.filter(is_read=False).count()

    cart = get_cart(request, create=False)

    return {
        'site': site,
        'unread_notifications': unread_notifications,
        'cart_count': cart.total_items if cart else 0,
    }