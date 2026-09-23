from datetime import timedelta, date
import json

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from api.models import (
    Product, ProductCategory, Promotion, Cart, CartItem, Order, OrderItem,
    Appointment, Service, SiteSettings, Notification,
)


@override_settings(ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1'])
class PromotionLogicTests(TestCase):
    def setUp(self):
        self.category = ProductCategory.objects.create(name='Teas')
        self.product = Product.objects.create(
            title='Herbal Tea', short_description='x', description='y',
            category=self.category, price=1000, stock_quantity=20,
        )

    def _promo(self, **overrides):
        data = dict(
            product=self.product, discount_type='percentage', discount_value=20,
            start_date=timezone.now() - timedelta(days=1),
            end_date=timezone.now() + timedelta(days=1),
            is_active=True,
        )
        data.update(overrides)
        return Promotion.objects.create(**data)

    def test_percentage_discount_computed_correctly(self):
        promo = self._promo(discount_type='percentage', discount_value=20)
        self.assertEqual(promo.promotional_price, 800)

    def test_fixed_discount_computed_correctly(self):
        promo = self._promo(discount_type='fixed', discount_value=150)
        self.assertEqual(promo.promotional_price, 850)

    def test_promotion_within_dates_is_live(self):
        promo = self._promo()
        self.assertTrue(promo.is_live)
        self.assertEqual(self.product.active_promotion, promo)
        self.assertEqual(self.product.display_price, promo.promotional_price)

    def test_expired_promotion_is_not_live_and_product_falls_back_to_regular_price(self):
        self._promo(start_date=timezone.now() - timedelta(days=10),
                    end_date=timezone.now() - timedelta(days=1))
        self.assertIsNone(self.product.active_promotion)
        self.assertEqual(self.product.display_price, self.product.price)
        self.assertFalse(self.product.has_discount)

    def test_upcoming_promotion_is_not_yet_live(self):
        promo = self._promo(start_date=timezone.now() + timedelta(days=1),
                             end_date=timezone.now() + timedelta(days=5))
        self.assertTrue(promo.is_upcoming)
        self.assertFalse(promo.is_live)
        self.assertIsNone(self.product.active_promotion)

    def test_paused_promotion_within_dates_is_not_live(self):
        promo = self._promo(is_active=False)
        self.assertFalse(promo.is_live)
        self.assertIsNone(self.product.active_promotion)

    def test_live_qs_excludes_everything_but_currently_live_promotions(self):
        live = self._promo()
        self._promo(start_date=timezone.now() + timedelta(days=1), end_date=timezone.now() + timedelta(days=5))
        self._promo(is_active=False)
        other_product = Product.objects.create(title='Other', short_description='x', description='y', price=500)
        self._promo(product=other_product, start_date=timezone.now() - timedelta(days=10),
                    end_date=timezone.now() - timedelta(days=1))
        qs = list(Promotion.live_qs())
        self.assertEqual(qs, [live])


@override_settings(ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1'])
class CartAndCheckoutTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            title='Bitter Kola Extract', short_description='x', description='y',
            price=2500, stock_quantity=10,
        )
        self.other_product = Product.objects.create(
            title='Moringa Powder', short_description='x', description='y',
            price=1500, stock_quantity=10,
        )

    def test_homepage_has_no_promotion_band_without_a_live_promotion(self):
        r = self.client.get('/')
        self.assertNotContains(r, 'Special Offers')

    def test_homepage_shows_promotion_band_when_live(self):
        Promotion.objects.create(
            product=self.product, discount_type='percentage', discount_value=15,
            start_date=timezone.now() - timedelta(days=1), end_date=timezone.now() + timedelta(days=1),
        )
        r = self.client.get('/')
        self.assertContains(r, 'Special Offers')

    def test_add_to_cart_creates_cart_and_item(self):
        r = self.client.post(f'/products/{self.product.slug}/add/', {'quantity': 2}, follow=True)
        self.assertEqual(r.status_code, 200)
        cart = Cart.objects.get()
        self.assertEqual(cart.total_items, 2)
        self.assertEqual(cart.subtotal, 5000)

    def test_adding_same_product_twice_increments_quantity_not_duplicate_rows(self):
        self.client.post(f'/products/{self.product.slug}/add/', {'quantity': 1})
        self.client.post(f'/products/{self.product.slug}/add/', {'quantity': 2})
        cart = Cart.objects.get()
        self.assertEqual(cart.cart_items.count(), 1)
        self.assertEqual(cart.cart_items.first().quantity, 3)

    def test_cart_reflects_promotional_price(self):
        Promotion.objects.create(
            product=self.product, discount_type='percentage', discount_value=20,
            start_date=timezone.now() - timedelta(days=1), end_date=timezone.now() + timedelta(days=1),
        )
        self.client.post(f'/products/{self.product.slug}/add/', {'quantity': 1})
        cart = Cart.objects.get()
        self.assertEqual(cart.cart_items.first().unit_price, 2000)

    def test_cart_update_changes_quantity(self):
        self.client.post(f'/products/{self.product.slug}/add/', {'quantity': 1})
        item = CartItem.objects.get()
        self.client.post(f'/cart/{item.pk}/update/', {'quantity': 5})
        item.refresh_from_db()
        self.assertEqual(item.quantity, 5)

    def test_cart_update_to_zero_removes_item(self):
        self.client.post(f'/products/{self.product.slug}/add/', {'quantity': 1})
        item = CartItem.objects.get()
        self.client.post(f'/cart/{item.pk}/update/', {'quantity': 0})
        self.assertFalse(CartItem.objects.filter(pk=item.pk).exists())

    def test_cart_remove_deletes_item(self):
        self.client.post(f'/products/{self.product.slug}/add/', {'quantity': 1})
        item = CartItem.objects.get()
        self.client.post(f'/cart/{item.pk}/remove/')
        self.assertFalse(CartItem.objects.filter(pk=item.pk).exists())

    def test_checkout_creates_multi_item_order_and_clears_cart(self):
        self.client.post(f'/products/{self.product.slug}/add/', {'quantity': 2})
        self.client.post(f'/products/{self.other_product.slug}/add/', {'quantity': 1})
        r = self.client.post('/checkout/', {
            'customer_name': 'Ada Obi', 'customer_phone': '08033332222',
            'customer_email': '', 'delivery_address': '', 'notes': '',
        })
        self.assertEqual(r.status_code, 200)
        order = Order.objects.get()
        self.assertEqual(order.items.count(), 2)
        self.assertEqual(order.subtotal, 2500 * 2 + 1500)
        self.assertEqual(order.status, 'pending')
        cart = Cart.objects.get()
        self.assertEqual(cart.total_items, 0)

    def test_checkout_with_empty_cart_redirects_to_products(self):
        r = self.client.post('/checkout/', {'customer_name': 'x', 'customer_phone': '08000000000'}, follow=True)
        self.assertRedirects(r, '/products/')

    def test_checkout_missing_phone_shows_validation_error(self):
        self.client.post(f'/products/{self.product.slug}/add/', {'quantity': 1})
        r = self.client.post('/checkout/', {'customer_name': 'Ada Obi', 'customer_phone': ''})
        self.assertEqual(Order.objects.count(), 0)
        self.assertContains(r, 'phone number')

    def test_order_number_is_unique_and_generated(self):
        self.client.post(f'/products/{self.product.slug}/add/', {'quantity': 1})
        self.client.post('/checkout/', {'customer_name': 'Ada Obi', 'customer_phone': '08033332222'})
        order = Order.objects.get()
        self.assertTrue(order.order_number)
        self.assertTrue(order.order_number.startswith('GHC'))

    def test_add_to_cart_clamps_quantity_to_stock(self):
        self.client.post(f'/products/{self.product.slug}/add/', {'quantity': 999})
        item = CartItem.objects.get()
        self.assertEqual(item.quantity, self.product.stock_quantity)

    def test_add_to_cart_floor_is_one_when_stock_not_tracked(self):
        untracked = Product.objects.create(
            title='Custom Blend', short_description='x', description='y',
            price=900, track_stock=False, stock_quantity=0,
        )
        self.client.post(f'/products/{untracked.slug}/add/', {'quantity': 0})
        item = CartItem.objects.get(product=untracked)
        self.assertEqual(item.quantity, 1)

    def test_cart_update_clamps_over_stock(self):
        self.client.post(f'/products/{self.product.slug}/add/', {'quantity': 1})
        item = CartItem.objects.get()
        self.client.post(f'/cart/{item.pk}/update/', {'quantity': 50})
        item.refresh_from_db()
        self.assertEqual(item.quantity, self.product.stock_quantity)

    def test_ajax_add_returns_json_without_redirect(self):
        r = self.client.post(f'/products/{self.product.slug}/add/', {'quantity': 2},
                             HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data['ok'])
        self.assertEqual(data['cart_total'], 2)
        self.assertEqual(Cart.objects.get().total_items, 2)

    def test_ajax_update_and_remove_return_json(self):
        self.client.post(f'/products/{self.product.slug}/add/', {'quantity': 3})
        item = CartItem.objects.get()
        r = self.client.post(f'/cart/{item.pk}/update/', {'quantity': 7},
                             HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(r.json()['ok'], True)
        self.assertEqual(Cart.objects.get().total_items, 7)
        r = self.client.post(f'/cart/{item.pk}/remove/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(r.json()['ok'], True)
        self.assertEqual(Cart.objects.get().total_items, 0)

    def test_checkout_offers_whatsapp_option_when_number_configured(self):
        site = SiteSettings.get()
        site.whatsapp_number = '+2348033334444'
        site.save()
        self.client.post(f'/products/{self.product.slug}/add/', {'quantity': 2})
        r = self.client.get(reverse('api:checkout'))
        self.assertContains(r, 'wa.me/2348033334444')
        self.assertContains(r, 'Send Order on WhatsApp')

    def test_checkout_hides_whatsapp_option_when_number_unconfigured(self):
        site = SiteSettings.get()
        site.whatsapp_number = ''
        site.save()
        self.client.post(f'/products/{self.product.slug}/add/', {'quantity': 1})
        r = self.client.get(reverse('api:checkout'))
        self.assertNotContains(r, 'Send Order on WhatsApp')

    def test_cart_whatsapp_message_has_items_but_no_prices(self):
        """The WhatsApp prefill carries product names + quantities and never money."""
        from urllib.parse import unquote
        from api.utils import build_cart_whatsapp_url
        self.client.post(f'/products/{self.product.slug}/add/', {'quantity': 2})
        self.client.post(f'/products/{self.other_product.slug}/add/', {'quantity': 1})
        site = SiteSettings.get()
        site.whatsapp_number = '+2348033334444'
        site.save()
        cart = Cart.objects.get()
        message = unquote(build_cart_whatsapp_url(cart).split('text=', 1)[1])
        self.assertIn('2x Bitter Kola Extract', message)
        self.assertIn('1x Moringa Powder', message)
        self.assertIn('Please share pricing and delivery details.', message)
        self.assertNotIn('2500', message)
        self.assertNotIn('1500', message)
        self.assertNotIn('₦', message)


@override_settings(ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1'])
class DashboardCommerceCrudTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user('shopadmin', 'shop@x.com', 'testpass123', is_staff=True, is_superuser=True)
        self.client.login(username='shopadmin', password='testpass123')
        self.product = Product.objects.create(title='Ginger Root', short_description='x', description='y', price=800)

    def test_category_create_via_dashboard(self):
        r = self.client.post('/dashboard/categories/add/', {
            'name': 'Roots & Powders', 'description': '', 'icon_name': 'Leaf',
            'sort_order': 0, 'is_active': 'on',
        })
        self.assertEqual(r.status_code, 302)
        self.assertTrue(ProductCategory.objects.filter(name='Roots & Powders').exists())

    def test_promotion_create_via_dashboard(self):
        r = self.client.post('/dashboard/promotions/add/', {
            'product': self.product.pk, 'discount_type': 'percentage', 'discount_value': 25,
            'start_date': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'end_date': (timezone.now() + timedelta(days=7)).strftime('%Y-%m-%dT%H:%M'),
            'is_active': 'on',
        })
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Promotion.objects.filter(product=self.product).exists())

    def test_promotion_end_before_start_rejected(self):
        r = self.client.post('/dashboard/promotions/add/', {
            'product': self.product.pk, 'discount_type': 'percentage', 'discount_value': 25,
            'start_date': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'end_date': (timezone.now() - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),
            'is_active': 'on',
        })
        self.assertEqual(Promotion.objects.count(), 0)
        self.assertContains(r, 'End date must be after')

    def test_order_status_change_via_dashboard(self):
        order = Order.objects.create(customer_name='Test Customer', customer_phone='08011112222', subtotal=800)
        OrderItem.objects.create(order=order, product=self.product, product_name='Ginger Root',
                                  unit_price=800, quantity=1)
        r = self.client.post(f'/dashboard/orders/{order.pk}/status/', {'status': 'confirmed'})
        self.assertEqual(r.status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.status, 'confirmed')


@override_settings(ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1'])
class BookingNotificationSettingsTests(TestCase):
    """
    The owner/staff-facing booking notifications (distinct from the
    customer-facing confirmation email, which always sends regardless).
    """
    def setUp(self):
        self.service = Service.objects.create(title='Cupping', short_description='x', description='y', price=3000)
        self.site = SiteSettings.get()

    def _book(self, **overrides):
        data = {
            'service': self.service.pk,
            'appointment_date': (date.today() + timedelta(days=3)).isoformat(),
            'preferred_time': '10:00',
            'contact_name': 'Notif Test',
            'contact_email': 'notiftest@x.com',
            'contact_phone': '08033334444',
            'notes': '',
        }
        data.update(overrides)
        return self.client.post('/book/', data, follow=True)

    def test_booking_notification_email_sent_by_default(self):
        self._book()
        self.assertEqual(len(mail.outbox), 2)  # customer confirmation + owner notification
        recipients = [r for m in mail.outbox for r in m.to]
        self.assertIn(self.site.contact_email, recipients)

    def test_booking_notification_email_uses_configured_recipient_over_contact_email(self):
        self.site.booking_notification_email = 'owner-alerts@x.com'
        self.site.save()
        self._book()
        recipients = [r for m in mail.outbox for r in m.to]
        self.assertIn('owner-alerts@x.com', recipients)
        self.assertNotIn(self.site.contact_email, recipients)

    def test_no_owner_notification_email_when_disabled(self):
        self.site.email_notifications_enabled = False
        self.site.save()
        self._book()
        # Customer confirmation still sends -- only the owner alert is gated.
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['notiftest@x.com'])

    def test_whatsapp_notification_not_attempted_when_disabled_by_default(self):
        # whatsapp_notifications_enabled defaults to False
        count_before = Notification.objects.filter(type='general').count()
        self._book()
        self.assertEqual(Notification.objects.filter(type='general').count(), count_before)

    def test_whatsapp_enabled_without_api_configured_files_failure_notification(self):
        self.site.whatsapp_notifications_enabled = True
        self.site.save()
        r = self._book()
        self.assertEqual(r.status_code, 200)  # booking flow itself doesn't break
        appt = Appointment.objects.get(contact_email='notiftest@x.com')
        self.assertTrue(appt.pk)  # booking still saved regardless of notification outcome
        self.assertTrue(
            Notification.objects.filter(type='general', title__icontains='WhatsApp').exists()
        )

    def test_whatsapp_service_reports_not_configured_without_env_vars(self):
        from api import whatsapp_service
        self.assertFalse(whatsapp_service.is_configured())
        sent, detail = whatsapp_service.send_business_whatsapp_message('2348012345678', 'test message')
        self.assertFalse(sent)
        self.assertIn('not configured', detail)

    def test_whatsapp_service_configured_when_env_vars_present(self):
        from django.test import override_settings as os_
        from api import whatsapp_service
        with os_(WHATSAPP_BUSINESS_API_TOKEN='fake-token', WHATSAPP_BUSINESS_PHONE_NUMBER_ID='123456'):
            self.assertTrue(whatsapp_service.is_configured())

    def test_whatsapp_service_uses_configured_api_version_in_url(self):
        from unittest import mock
        from django.test import override_settings as os_
        from api import whatsapp_service
        captured = {}

        def fake_post(url, **kwargs):
            captured['url'] = url
            resp = mock.Mock()
            resp.status_code = 200
            return resp

        with os_(
            WHATSAPP_BUSINESS_API_TOKEN='fake-token',
            WHATSAPP_BUSINESS_PHONE_NUMBER_ID='123456',
            WHATSAPP_API_VERSION='v99.0',
        ), mock.patch('api.whatsapp_service.requests.post', side_effect=fake_post):
            sent, _detail = whatsapp_service.send_business_whatsapp_message('2348012345678', 'hi')
        self.assertTrue(sent)
        self.assertIn('/v99.0/123456/messages', captured['url'])

    def test_effective_booking_email_falls_back_to_contact_email(self):
        self.site.booking_notification_email = ''
        self.site.contact_email = 'fallback@x.com'
        self.site.save()
        self.assertEqual(self.site.effective_booking_email, 'fallback@x.com')

    def test_effective_booking_whatsapp_falls_back_to_whatsapp_number(self):
        self.site.booking_whatsapp_number = ''
        self.site.whatsapp_number = '2348011112222'
        self.site.save()
        self.assertEqual(self.site.effective_booking_whatsapp, '2348011112222')


@override_settings(ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1'])
class PublicPriceHidingTests(TestCase):
    """The public shop shows no numeric prices anywhere â€” enquiry is the conversion path."""

    PRICE_FRAGMENTS = ('&#8358;', '\u20a6', 'NGN')

    def setUp(self):
        self.category = ProductCategory.objects.create(name='Teas')
        self.product = Product.objects.create(
            title='Herbal Tea', short_description='x', description='y',
            category=self.category, price=1000, stock_quantity=20,
        )
        self.service = Service.objects.create(title='Cupping', short_description='x', description='y', price=3000)
        Promotion.objects.create(
            product=self.product, discount_type='percentage', discount_value=15,
            start_date=timezone.now() - timedelta(days=1), end_date=timezone.now() + timedelta(days=1),
        )
        self.fragments = lambda r: [self.assertNotContains(r, f) for f in self.PRICE_FRAGMENTS]

    def test_home_page_has_no_price_text(self):
        self.fragments(self.client.get(reverse('api:home')))

    def test_product_list_and_detail_have_no_price_text(self):
        self.fragments(self.client.get(reverse('api:products')))
        detail = self.client.get(reverse('api:product_detail', args=[self.product.slug]))
        self.fragments(detail)
        self.assertContains(detail, 'Contact for Enquiry')

    def test_cart_and_checkout_have_no_price_text(self):
        self.client.post(reverse('api:cart_add', args=[self.product.slug]), {'quantity': 2})
        self.fragments(self.client.get(reverse('api:cart')))
        self.fragments(self.client.get(reverse('api:checkout')))
        # Even the concrete amount never leaks, only price-leak wording patterns.
        checkout = self.client.get(reverse('api:checkout'))
        self.assertNotContains(checkout, '1000')
        self.assertNotContains(checkout, '1700')

    def test_order_success_has_no_price_text(self):
        self.client.post(reverse('api:cart_add', args=[self.product.slug]), {'quantity': 2})
        response = self.client.post(reverse('api:checkout'), {
            'customer_name': 'Ada Obi', 'customer_phone': '08033332222',
        })
        self.fragments(response)

    def test_services_list_and_detail_have_no_price_text(self):
        self.fragments(self.client.get(reverse('api:services')))
        self.fragments(self.client.get(reverse('api:service_detail', args=[self.service.slug])))


@override_settings(ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1'])
class PromoVideoSectionTests(TestCase):
    def setUp(self):
        self.site = SiteSettings.get()

    def test_homepage_hides_section_when_disabled(self):
        r = self.client.get(reverse('api:home'))
        self.assertNotContains(r, 'promovideo-modal')
        self.assertNotContains(r, 'Watch the film')

    def test_homepage_shows_section_when_enabled(self):
        self.site.promo_video_enabled = True
        self.site.promo_video_url = 'https://www.youtube.com/embed/dQw4w9WgXcQ'
        self.site.promo_video_title = 'Inside Our Workshop'
        self.site.promo_video_cta_label = 'Book a Consultation'
        self.site.promo_video_cta_url = '/book/'
        self.site.save()
        r = self.client.get(reverse('api:home'))
        self.assertContains(r, 'promovideo-modal')
        self.assertContains(r, 'Watch the film')
        self.assertContains(r, 'Inside Our Workshop')
        self.assertContains(r, 'Book a Consultation')
        self.assertContains(r, 'https://www.youtube.com/embed/dQw4w9WgXcQ')

    def test_homepage_renders_poster_fallback_without_upload(self):
        """No poster uploaded yet → the section still renders (gradient + play)."""
        self.site.promo_video_enabled = True
        self.site.promo_video_url = 'https://vimeo.com/123456789'
        self.site.promo_video_poster = None
        self.site.save()
        r = self.client.get(reverse('api:home'))
        self.assertContains(r, 'promovideo-modal')
        self.assertContains(r, 'Watch the film')


@override_settings(ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1'])
class ProductEnquiryTests(TestCase):
    def setUp(self):
        self.site = SiteSettings.get()
        self.site.contact_email = 'owner@test.com'
        self.site.save()
        self.product = Product.objects.create(
            title='Bitter Kola Extract', short_description='x', description='y',
            price=2500, stock_quantity=10,
        )

    def _valid_data(self):
        return {
            'product_id': self.product.pk,
            'product_name': self.product.title,
            'quantity': 2,
            'name': 'Dele Musa',
            'phone': '08055556666',
            'email': '',
            'message': 'How much is this?',
        }

    def test_enquiry_creates_inquiry_with_product_context_notification_and_owner_email(self):
        r = self.client.post(reverse('api:product_enquiry', args=[self.product.slug]), self._valid_data())
        self.assertEqual(r.status_code, 200)
        from api.models import Inquiry
        inquiry = Inquiry.objects.get()
        self.assertIn(self.product.title, inquiry.message)
        self.assertIn('(quantity: 2)', inquiry.message)
        notification = Notification.objects.get(type='inquiry')
        self.assertEqual(notification.url, f'/dashboard/messages/{inquiry.pk}/')
        self.assertEqual(len(mail.outbox), 1)  # owner email (enquiry toggles default on)
        self.assertIn('owner@test.com', mail.outbox[0].to)

    def test_enquiry_missing_phone_rerenders_detail_and_creates_nothing(self):
        data = self._valid_data()
        del data['phone']
        r = self.client.post(reverse('api:product_enquiry', args=[self.product.slug]), data)
        self.assertEqual(r.status_code, 200)
        from api.models import Inquiry
        self.assertEqual(Inquiry.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)
        self.assertContains(r, 'Contact for Enquiry')

    def test_enquiry_email_disabled_silences_owner_email(self):
        self.site.enquiry_email_notifications_enabled = False
        self.site.save()
        self.client.post(reverse('api:product_enquiry', args=[self.product.slug]), self._valid_data())
        from api.models import Inquiry
        self.assertTrue(Inquiry.objects.exists())
        self.assertEqual(len(mail.outbox), 0)

    def test_enquiry_record_survives_email_failure(self):
        """A failing SMTP backend must not lose the customer's enquiry."""
        from unittest import mock
        from api.models import Inquiry
        with mock.patch('api.email_service.EmailMultiAlternatives.send',
                        side_effect=RuntimeError('smtp down')):
            r = self.client.post(reverse('api:product_enquiry', args=[self.product.slug]), self._valid_data())
        self.assertEqual(r.status_code, 200)
        self.assertTrue(Inquiry.objects.exists())
        # A 'general' bell row flags the failed channel without losing the enquiry.
        from api.models import Notification
        self.assertTrue(Notification.objects.filter(type='general', title__icontains='email').exists())


@override_settings(ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1'])
class NotificationAndPushTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user('staff1', 'staff@x.com', 'testpass123', is_superuser=True)

    def test_create_notification_stores_url(self):
        from api.utils import create_notification
        create_notification('order', 'New Order', 'Order placed', url='/dashboard/orders/12/')
        n = Notification.objects.get(type='order')
        self.assertEqual(n.url, '/dashboard/orders/12/')

    def test_notifications_list_links_records_with_url(self):
        self.client.login(username='staff1', password='testpass123')
        Notification.objects.create(type='inquiry', title='A', message='m', url='/dashboard/messages/5/')
        Notification.objects.create(type='general', title='B', message='m')
        r = self.client.get(reverse('dashboard:notifications'))
        self.assertContains(r, 'View details')
        self.assertContains(r, '/dashboard/messages/5/')

    def test_push_subscription_created_and_retrieved(self):
        from api.models import PushSubscription
        push = PushSubscription.objects.create(
            user=self.staff, endpoint='https://push.example.com/endpoint/device1',
            p256dh='abc=', auth='def=',
        )
        self.assertEqual(PushSubscription.objects.get(pk=push.pk).user, self.staff)
        self.assertIn('Push device for', str(push))

    def test_push_settings_requires_push_vapid_config(self):
        self.client.login(username='staff1', password='testpass123')
        r = self.client.get(reverse('dashboard:push_settings'))
        self.assertIn('configured', r.content.decode().lower())  # clean message, not a 500

    def test_full_push_pipeline_pushes_correct_payload(self):
        """Notification -> bell row + mocked pywebpush delivery end-to-end."""
        from unittest import mock
        from django.test import override_settings as os_
        from api.models import PushSubscription
        from api.utils import create_notification

        sub = PushSubscription.objects.create(
            user=self.staff,
            endpoint='https://push.example.com/endpoint/device1',
            p256dh='fakep256dh==', auth='fakeauth==',
        )

        with os_(
            VAPID_PUBLIC_KEY='fake-public-key',
            VAPID_PRIVATE_KEY='fake-private-key',
            VAPID_CLAIMS_EMAIL='owner@test.com',
        ), mock.patch('pywebpush.webpush') as wp:
            create_notification('order', 'New Order', 'A new order.', url='/dashboard/orders/7/')

        notification = Notification.objects.get(type='order')
        self.assertEqual(notification.url, '/dashboard/orders/7/')
        self.assertEqual(wp.call_count, 1)
        kwargs = wp.call_args.kwargs
        self.assertEqual(
            kwargs['subscription_info'],
            {'endpoint': sub.endpoint, 'keys': {'p256dh': 'fakep256dh==', 'auth': 'fakeauth=='}},
        )
        sent = json.loads(kwargs['data'])
        self.assertEqual(sent['title'], 'New Order')
        self.assertEqual(sent['message'], 'A new order.')
        self.assertEqual(sent['url'], '/dashboard/orders/7/')
        self.assertIn('sound', sent)

    def test_send_to_subscription_marks_last_used(self):
        from unittest import mock
        from django.test import override_settings as os_
        from api.models import PushSubscription
        from api.push_service import send_to_subscription

        sub = PushSubscription.objects.create(
            user=self.staff,
            endpoint='https://push.example.com/endpoint/device2',
            p256dh='fake2==', auth='fake2auth==',
        )
        with os_(
            VAPID_PUBLIC_KEY='fake-public-key',
            VAPID_PRIVATE_KEY='fake-private-key',
            VAPID_CLAIMS_EMAIL='owner@test.com',
        ), mock.patch('pywebpush.webpush'):
            ok, detail = send_to_subscription(sub, 'Alert', 'Hi', url='/dashboard/notifications/')
        self.assertTrue(ok)
        self.assertEqual(detail, 'sent')
        sub.refresh_from_db()
        self.assertIsNotNone(sub.last_used_at)

    def test_send_to_subscription_drops_stale_endpoint_on_410(self):
        from unittest import mock
        from unittest.mock import MagicMock
        from django.test import override_settings as os_
        from api.models import PushSubscription
        from api.push_service import send_to_subscription
        from pywebpush import WebPushException

        sub = PushSubscription.objects.create(
            user=self.staff,
            endpoint='https://push.example.com/endpoint/device3',
            p256dh='fake3==', auth='fake3auth==',
        )
        res = MagicMock()
        res.status_code = 410

        def boom(**kwargs):
            raise WebPushException('gone', response=res)

        with os_(
            VAPID_PUBLIC_KEY='fake-public-key',
            VAPID_PRIVATE_KEY='fake-private-key',
            VAPID_CLAIMS_EMAIL='owner@test.com',
        ), mock.patch('pywebpush.webpush', side_effect=boom):
            ok, detail = send_to_subscription(sub, 'Alert', 'Hi')
        self.assertFalse(ok)
        self.assertIn('subscription removed', detail)
        self.assertFalse(PushSubscription.objects.filter(pk=sub.pk).exists())

