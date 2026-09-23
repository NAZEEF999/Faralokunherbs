from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from api.models import Product, BlogPost
from .models import AnatomyTopic, HealthCondition, Herb


@override_settings(ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1'])
class HealthLibraryPublicPagesTests(TestCase):
    def setUp(self):
        self.topic = AnatomyTopic.objects.create(
            name='Femur', system='skeletal', short_description='The thigh bone.',
            function='Supports body weight.', common_issues='Fractures\nOsteoporosis',
        )
        self.condition = HealthCondition.objects.create(
            name='Common Cold', overview='A mild viral infection.',
            symptoms='Runny nose\nCough', causes='Viruses',
        )
        self.herb = Herb.objects.create(
            common_name='Ginger', scientific_name='Zingiber officinale',
            description='A flowering plant.', traditional_uses='Nausea relief\nDigestion',
        )

    def test_index_page_loads(self):
        r = self.client.get('/health-library/')
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Health Library')

    def test_index_shows_disclaimer(self):
        r = self.client.get('/health-library/')
        self.assertContains(r, 'not medical advice')

    def test_anatomy_list_shows_active_topic(self):
        r = self.client.get('/health-library/anatomy/')
        self.assertContains(r, 'Femur')

    def test_anatomy_list_hides_inactive_topic(self):
        self.topic.is_active = False
        self.topic.save()
        r = self.client.get('/health-library/anatomy/')
        self.assertNotContains(r, 'Femur')

    def test_anatomy_list_filters_by_system(self):
        AnatomyTopic.objects.create(name='Heart', system='organs', short_description='Pumps blood.')
        r = self.client.get('/health-library/anatomy/?system=organs')
        self.assertContains(r, 'Heart')
        self.assertNotContains(r, 'Femur')

    def test_anatomy_detail_shows_function_and_issues(self):
        r = self.client.get(f'/health-library/anatomy/{self.topic.slug}/')
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Supports body weight')
        self.assertContains(r, 'Fractures')

    def test_condition_list_shows_condition(self):
        r = self.client.get('/health-library/conditions/')
        self.assertContains(r, 'Common Cold')

    def test_condition_list_search(self):
        HealthCondition.objects.create(name='Malaria', overview='A mosquito-borne disease.')
        r = self.client.get('/health-library/conditions/?q=malaria')
        self.assertContains(r, 'Malaria')
        self.assertNotContains(r, 'Common Cold')

    def test_condition_detail_shows_symptoms(self):
        r = self.client.get(f'/health-library/conditions/{self.condition.slug}/')
        self.assertContains(r, 'Runny nose')

    def test_condition_detail_shows_related_herb(self):
        self.condition.related_herbs.add(self.herb)
        r = self.client.get(f'/health-library/conditions/{self.condition.slug}/')
        self.assertContains(r, 'Ginger')

    def test_herb_list_shows_herb(self):
        r = self.client.get('/health-library/herbs/')
        self.assertContains(r, 'Ginger')
        self.assertContains(r, 'Zingiber officinale')

    def test_herb_detail_shows_traditional_uses(self):
        r = self.client.get(f'/health-library/herbs/{self.herb.slug}/')
        self.assertContains(r, 'Nausea relief')

    def test_herb_detail_shows_related_product(self):
        product = Product.objects.create(title='Ginger Tea', short_description='x', description='y', price=1000)
        self.herb.related_products.add(product)
        r = self.client.get(f'/health-library/herbs/{self.herb.slug}/')
        self.assertContains(r, 'Ginger Tea')

    def test_wellness_list_shows_only_wellness_category_posts(self):
        BlogPost.objects.create(title='Sleep Better Tonight', excerpt='x', content='y',
                                 category='Wellness', is_published=True)
        BlogPost.objects.create(title='Company News', excerpt='x', content='y',
                                 category='News', is_published=True)
        r = self.client.get('/health-library/wellness/')
        self.assertContains(r, 'Sleep Better Tonight')
        self.assertNotContains(r, 'Company News')

    def test_inactive_condition_returns_404(self):
        self.condition.is_active = False
        self.condition.save()
        r = self.client.get(f'/health-library/conditions/{self.condition.slug}/')
        self.assertEqual(r.status_code, 404)

    def test_health_library_in_sitemap(self):
        r = self.client.get('/sitemap.xml')
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, '/health-library/')


@override_settings(ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1'])
class HealthLibraryDashboardCrudTests(TestCase):
    def setUp(self):
        from dashboard.models import StaffAccess
        self.owner = User.objects.create_user('hlowner', 'hl@x.com', 'testpass123')
        StaffAccess.objects.create(user=self.owner, role='owner')
        self.product_manager = User.objects.create_user('hlpm', 'hlpm@x.com', 'testpass123')
        StaffAccess.objects.create(user=self.product_manager, role='product_manager')

    def test_owner_can_create_anatomy_topic(self):
        self.client.login(username='hlowner', password='testpass123')
        r = self.client.post('/dashboard/health/anatomy/add/', {
            'name': 'Tibia', 'system': 'skeletal', 'short_description': 'The shin bone.',
            'function': '', 'common_issues': '', 'general_info': '', 'sort_order': 0, 'is_active': 'on',
        })
        self.assertEqual(r.status_code, 302)
        self.assertTrue(AnatomyTopic.objects.filter(name='Tibia').exists())

    def test_owner_can_create_condition(self):
        self.client.login(username='hlowner', password='testpass123')
        r = self.client.post('/dashboard/health/conditions/add/', {
            'name': 'Migraine', 'overview': 'A neurological condition.', 'causes': '',
            'symptoms': '', 'prevention': '', 'lifestyle_tips': '', 'treatment_info': '',
            'seek_care_info': '', 'related_herbs': [], 'is_active': 'on', 'sort_order': 0,
        })
        self.assertEqual(r.status_code, 302)
        self.assertTrue(HealthCondition.objects.filter(name='Migraine').exists())

    def test_owner_can_create_herb(self):
        self.client.login(username='hlowner', password='testpass123')
        r = self.client.post('/dashboard/health/herbs/add/', {
            'common_name': 'Turmeric', 'scientific_name': 'Curcuma longa', 'description': 'A root.',
            'traditional_uses': '', 'compounds_info': '', 'preparation_info': '', 'safety_info': '',
            'interactions_info': '', 'precautions': '', 'related_products': [],
            'is_active': 'on', 'sort_order': 0,
        })
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Herb.objects.filter(common_name='Turmeric').exists())

    def test_product_manager_cannot_access_health_library_dashboard(self):
        self.client.login(username='hlpm', password='testpass123')
        r = self.client.get('/dashboard/health/anatomy/', follow=True)
        self.assertContains(r, 'have access to that area')

    def test_anonymous_cannot_access_health_library_dashboard(self):
        r = self.client.get('/dashboard/health/conditions/')
        self.assertEqual(r.status_code, 302)
