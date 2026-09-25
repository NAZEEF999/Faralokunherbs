from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import AnatomyTopic, HealthCondition, Herb


@admin.register(AnatomyTopic)
class AnatomyTopicAdmin(ModelAdmin):
    list_display  = ['name', 'system', 'sort_order', 'is_active']
    list_filter   = ['system', 'is_active']
    search_fields = ['name', 'short_description']
    prepopulated_fields = {'slug': ('name',)}
    ordering      = ['system', 'sort_order', 'name']
    fieldsets = (
        (None, {'fields': ('name', 'slug', 'system', 'sort_order')}),
        ('Image', {'fields': ('image', 'local_image')}),
        ('Content', {'fields': ('short_description', 'function', 'common_issues', 'general_info')}),
        ('Visibility', {'fields': ('is_active',)}),
    )


@admin.register(HealthCondition)
class HealthConditionAdmin(ModelAdmin):
    list_display  = ['name', 'is_featured', 'is_active', 'sort_order']
    list_filter   = ['is_featured', 'is_active']
    search_fields = ['name', 'overview']
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ['related_herbs']
    ordering      = ['sort_order', 'name']
    fieldsets = (
        (None, {'fields': ('name', 'slug', 'sort_order')}),
        ('Image', {'fields': ('image', 'local_image')}),
        ('Content', {'fields': ('overview', 'causes', 'symptoms', 'prevention',
                                'lifestyle_tips', 'treatment_info', 'seek_care_info')}),
        ('Relations', {'fields': ('related_herbs',)}),
        ('Visibility', {'fields': ('is_featured', 'is_active')}),
    )


@admin.register(Herb)
class HerbAdmin(ModelAdmin):
    list_display  = ['common_name', 'scientific_name', 'is_featured', 'is_active', 'sort_order']
    list_filter   = ['is_featured', 'is_active']
    search_fields = ['common_name', 'scientific_name', 'description']
    prepopulated_fields = {'slug': ('common_name',)}
    filter_horizontal = ['related_products']
    ordering      = ['sort_order', 'common_name']
    fieldsets = (
        (None, {'fields': ('common_name', 'scientific_name', 'slug', 'sort_order')}),
        ('Image', {'fields': ('image', 'local_image')}),
        ('Content', {'fields': ('description', 'traditional_uses', 'compounds_info',
                                'preparation_info', 'safety_info', 'interactions_info', 'precautions')}),
        ('Relations', {'fields': ('related_products',)}),
        ('Visibility', {'fields': ('is_featured', 'is_active')}),
    )
