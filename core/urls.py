from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from django.http import HttpResponse

from api.sitemaps import sitemaps


def robots_txt(request):
    # Domain is derived from the actual request, matching the sitemap's own
    # domain resolution -- never hardcoded, so it's automatically correct
    # whatever host the site is actually served from (dev/staging/prod).
    sitemap_url = request.build_absolute_uri('/sitemap.xml')
    lines = [
        'User-agent: *',
        'Allow: /',
        'Disallow: /dashboard/',
        'Disallow: /portal/',
        'Disallow: /admin/',
        '',
        f'Sitemap: {sitemap_url}',
    ]
    return HttpResponse('\n'.join(lines), content_type='text/plain')


def favicon_ico(request):
    # Browsers request /favicon.ico by convention. Serve the generated ICO
    # through the normal static pipeline instead of 404ing.
    from django.http import HttpResponseRedirect
    from django.templatetags.static import static
    return HttpResponseRedirect(static('img/favicon.ico'))


urlpatterns = [
    path('admin/',      admin.site.urls),
    path('portal/',     include('accounts.urls',   namespace='accounts')),
    path('dashboard/',  include('dashboard.urls',  namespace='dashboard')),
    path('health-library/', include('health.urls', namespace='health')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
    path('robots.txt',  robots_txt, name='robots_txt'),
    path('favicon.ico', favicon_ico, name='favicon_ico'),
    path('',            include('api.urls',        namespace='api')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
