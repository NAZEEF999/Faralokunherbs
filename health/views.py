from django.shortcuts import render, get_object_or_404

from api.models import SiteSettings, BlogPost
from .models import AnatomyTopic, HealthCondition, Herb


def index(request):
    site = SiteSettings.get()
    return render(request, 'health/index.html', {
        'anatomy_count':   AnatomyTopic.objects.filter(is_active=True).count(),
        'condition_count': HealthCondition.objects.filter(is_active=True).count(),
        'herb_count':      Herb.objects.filter(is_active=True).count(),
        'featured_conditions': HealthCondition.objects.filter(is_active=True, is_featured=True)[:3],
        'featured_herbs':      Herb.objects.filter(is_active=True, is_featured=True)[:3],
        'wellness_posts':      BlogPost.objects.filter(is_published=True, category__iexact='Wellness')[:3],
        'page_title': f"Health Library | {site.site_name}",
        'page_description': f"Educational anatomy, health condition, and herbal information from {site.site_name}.",
    })


def anatomy_list(request):
    site = SiteSettings.get()
    topics = AnatomyTopic.objects.filter(is_active=True)
    system = request.GET.get('system', '')
    if system:
        topics = topics.filter(system=system)
    systems_present = AnatomyTopic.SYSTEM_CHOICES
    return render(request, 'health/anatomy_list.html', {
        'topics': topics, 'systems': systems_present, 'active_system': system,
        'page_title': f"Human Anatomy | {site.site_name}",
        'page_description': f"Explore the human body — bones, muscles, organs and more, from {site.site_name}.",
    })


def anatomy_detail(request, slug):
    topic = get_object_or_404(AnatomyTopic, slug=slug, is_active=True)
    related = AnatomyTopic.objects.filter(is_active=True, system=topic.system).exclude(pk=topic.pk)[:4]
    site = SiteSettings.get()
    return render(request, 'health/anatomy_detail.html', {
        'topic': topic, 'related_topics': related,
        'page_title': f"{topic.name} | {site.site_name}",
        'page_description': topic.short_description[:160],
    })


def conditions_list(request):
    site = SiteSettings.get()
    conditions = HealthCondition.objects.filter(is_active=True)
    q = request.GET.get('q', '').strip()
    if q:
        conditions = conditions.filter(name__icontains=q)
    return render(request, 'health/conditions_list.html', {
        'conditions': conditions, 'q': q,
        'page_title': f"Health Conditions | {site.site_name}",
        'page_description': f"Educational information on common health conditions from {site.site_name}.",
    })


def condition_detail(request, slug):
    condition = get_object_or_404(
        HealthCondition.objects.prefetch_related('related_herbs'), slug=slug, is_active=True)
    site = SiteSettings.get()
    return render(request, 'health/condition_detail.html', {
        'condition': condition,
        'page_title': f"{condition.name} | {site.site_name}",
        'page_description': condition.overview[:160],
    })


def herbs_list(request):
    site = SiteSettings.get()
    herbs = Herb.objects.filter(is_active=True)
    q = request.GET.get('q', '').strip()
    if q:
        herbs = herbs.filter(common_name__icontains=q)
    return render(request, 'health/herbs_list.html', {
        'herbs': herbs, 'q': q,
        'page_title': f"Herbs & Ingredients | {site.site_name}",
        'page_description': f"Traditional herbs and natural ingredients explained by {site.site_name}.",
    })


def herb_detail(request, slug):
    herb = get_object_or_404(
        Herb.objects.prefetch_related('related_products', 'related_conditions'), slug=slug, is_active=True)
    site = SiteSettings.get()
    return render(request, 'health/herb_detail.html', {
        'herb': herb,
        'page_title': f"{herb.common_name} | {site.site_name}",
        'page_description': herb.description[:160],
    })


def wellness_list(request):
    site = SiteSettings.get()
    posts = BlogPost.objects.filter(is_published=True, category__iexact='Wellness')
    return render(request, 'health/wellness_list.html', {
        'posts': posts,
        'page_title': f"Wellness | {site.site_name}",
        'page_description': f"Nutrition, sleep, exercise and lifestyle guidance from {site.site_name}.",
    })
