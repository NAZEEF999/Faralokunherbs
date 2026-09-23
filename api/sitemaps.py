from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Service, Product, BlogPost
from health.models import AnatomyTopic, HealthCondition, Herb


class StaticViewSitemap(Sitemap):
    """
    Public, indexable static pages only. Deliberately does NOT include
    /dashboard/, /portal/, /accounts/login/, /accounts/register/, or any
    other private/internal/auth-gated route.
    """
    changefreq = 'weekly'

    _priority_overrides = {'api:home': 1.0}

    def items(self):
        return [
            'api:home', 'api:about', 'api:services', 'api:products',
            'api:blog', 'api:contact', 'api:book', 'health:index',
            'health:anatomy_list', 'health:conditions_list', 'health:herbs_list',
            'health:wellness_list',
        ]

    def location(self, item):
        return reverse(item)

    def priority(self, item):
        return self._priority_overrides.get(item, 0.7)


class ServiceSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.8

    def items(self):
        return Service.objects.filter(active=True)

    def location(self, obj):
        return reverse('api:service_detail', args=[obj.slug])

    def lastmod(self, obj):
        return obj.updated_at


class ProductSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.6

    def items(self):
        return Product.objects.filter(active=True)

    def location(self, obj):
        return reverse('api:product_detail', args=[obj.slug])

    def lastmod(self, obj):
        return obj.updated_at


class BlogSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.5

    def items(self):
        return BlogPost.objects.filter(is_published=True)

    def location(self, obj):
        return reverse('api:blog_detail', args=[obj.slug])

    def lastmod(self, obj):
        return obj.updated_at


class AnatomySitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.4

    def items(self):
        return AnatomyTopic.objects.filter(is_active=True)

    def location(self, obj):
        return reverse('health:anatomy_detail', args=[obj.slug])

    def lastmod(self, obj):
        return obj.updated_at


class ConditionSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.4

    def items(self):
        return HealthCondition.objects.filter(is_active=True)

    def location(self, obj):
        return reverse('health:condition_detail', args=[obj.slug])

    def lastmod(self, obj):
        return obj.updated_at


class HerbSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.4

    def items(self):
        return Herb.objects.filter(is_active=True)

    def location(self, obj):
        return reverse('health:herb_detail', args=[obj.slug])

    def lastmod(self, obj):
        return obj.updated_at


sitemaps = {
    'static':     StaticViewSitemap,
    'services':   ServiceSitemap,
    'products':   ProductSitemap,
    'blog':       BlogSitemap,
    'anatomy':    AnatomySitemap,
    'conditions': ConditionSitemap,
    'herbs':      HerbSitemap,
}
