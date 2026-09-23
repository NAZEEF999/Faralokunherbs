from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('login/',  views.dashboard_login,  name='login'),
    path('logout/', views.dashboard_logout, name='logout'),
    path('login/2fa/', views.two_factor_challenge, name='two_factor_challenge'),
    path('password-reset/', views.password_reset_request, name='password_reset_request'),
    path('password-reset/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('',         views.overview, name='overview'),

    path('account-security/', views.account_security, name='account_security'),
    path('account-security/logout-other-sessions/', views.logout_other_sessions, name='logout_other_sessions'),
    path('account-security/2fa/setup/', views.two_factor_setup, name='two_factor_setup'),
    path('account-security/2fa/recovery-codes/', views.two_factor_recovery_codes, name='two_factor_recovery_codes'),
    path('account-security/2fa/regenerate-codes/', views.two_factor_regenerate_codes, name='two_factor_regenerate_codes'),
    path('account-security/2fa/disable/', views.two_factor_disable, name='two_factor_disable'),

    path('appointments/',                    views.appointments_list,          name='appointments'),
    path('appointments/<int:pk>/',           views.appointment_detail,         name='appointment_detail'),
    path('appointments/<int:pk>/status/',    views.appointment_update_status,  name='appointment_update_status'),

    path('patients/',            views.patients_list,  name='patients'),
    path('patients/<int:pk>/',   views.patient_detail,  name='patient_detail'),

    path('messages/',            views.messages_list,  name='messages'),
    path('messages/<int:pk>/',   views.message_detail,  name='message_detail'),

    path('notifications/',                       views.notifications_list,          name='notifications'),
    path('notifications/<int:pk>/read/',         views.notification_mark_read,      name='notification_mark_read'),
    path('notifications/mark-all-read/',         views.notifications_mark_all_read, name='notifications_mark_all_read'),

    path('orders/',                     views.orders_list,         name='orders'),
    path('orders/<int:pk>/',            views.order_detail,        name='order_detail'),
    path('orders/<int:pk>/status/',     views.order_update_status, name='order_update_status'),

    path('services/',                 views.services_list, name='services'),
    path('services/add/',             views.service_edit,  name='service_add'),
    path('services/<int:pk>/edit/',   views.service_edit,  name='service_edit'),

    path('categories/',               views.categories_list, name='categories'),
    path('categories/add/',           views.category_edit,   name='category_add'),
    path('categories/<int:pk>/edit/', views.category_edit,   name='category_edit'),

    path('products/',                 views.products_list, name='products'),
    path('products/add/',             views.product_edit,  name='product_add'),
    path('products/<int:pk>/edit/',   views.product_edit,  name='product_edit'),

    path('promotions/',               views.promotions_list, name='promotions'),
    path('promotions/add/',           views.promotion_edit,  name='promotion_add'),
    path('promotions/<int:pk>/edit/', views.promotion_edit,  name='promotion_edit'),


    path('blog/',                 views.blog_list, name='blog'),
    path('blog/add/',             views.blog_edit, name='blog_add'),
    path('blog/<int:pk>/edit/',   views.blog_edit, name='blog_edit'),

    path('health/anatomy/',                  views.health_anatomy_list, name='health_anatomy'),
    path('health/anatomy/add/',              views.health_anatomy_edit, name='health_anatomy_add'),
    path('health/anatomy/<int:pk>/edit/',    views.health_anatomy_edit, name='health_anatomy_edit'),
    path('health/conditions/',               views.health_conditions_list, name='health_conditions'),
    path('health/conditions/add/',           views.health_condition_edit,  name='health_condition_add'),
    path('health/conditions/<int:pk>/edit/', views.health_condition_edit,  name='health_condition_edit'),
    path('health/herbs/',                    views.health_herbs_list, name='health_herbs'),
    path('health/herbs/add/',                views.health_herb_edit,  name='health_herb_add'),
    path('health/herbs/<int:pk>/edit/',      views.health_herb_edit,  name='health_herb_edit'),
    path('testimonials/',                     views.testimonials_list,             name='testimonials'),
    path('testimonials/<int:pk>/toggle/',     views.testimonial_toggle_approved,   name='testimonial_toggle'),
    path('subscribers/',   views.subscribers_list,  name='subscribers'),

    path('settings/', views.site_settings, name='site_settings'),

    # Web App Manifest + Service Worker (public, no auth -- PWA requirement)
    path('manifest.webmanifest', views.pwa_manifest,     name='pwa_manifest'),
    path('sw.js',                views.pwa_service_worker, name='pwa_service_worker'),
    # Web Push (staff only)
    path('push/settings/',     views.push_settings,     name='push_settings'),
    path('push/subscribe/',    views.push_subscribe,    name='push_subscribe'),
    path('push/unsubscribe/',  views.push_unsubscribe,  name='push_unsubscribe'),
    path('push/test/',         views.push_test,         name='push_test'),

    path('staff/',               views.staff_list, name='staff'),
    path('staff/add/',           views.staff_add,  name='staff_add'),
    path('staff/<int:pk>/edit/', views.staff_edit,  name='staff_edit'),
]
