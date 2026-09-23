"""
Session-based shopping cart helper.

No customer account is required to buy products (matches the rest of the
site — booking never requires an account either). The cart is tied to the
visitor's session key, created on first use.
"""
from .models import Cart


def get_cart(request, create=True):
    """
    Returns the Cart for the current session, creating both the session
    and the Cart row on first use. Pass create=False for read-only lookups
    (e.g. the cart badge in the navbar) where we don't want to create a
    session/Cart just because a page was viewed.
    """
    if not request.session.session_key:
        if not create:
            return None
        request.session.create()

    session_key = request.session.session_key
    if not session_key:
        return None

    if create:
        cart, _ = Cart.objects.get_or_create(session_key=session_key)
        return cart

    return Cart.objects.filter(session_key=session_key).first()
