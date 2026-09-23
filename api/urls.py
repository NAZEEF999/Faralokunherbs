from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    path('',                              views.home,                    name='home'),
    path('services/',                     views.services,                name='services'),
    path('services/<slug:slug>/',         views.service_detail,          name='service_detail'),
    path('products/',                     views.products,                name='products'),
    path('products/<slug:slug>/',         views.product_detail,          name='product_detail'),
    path('products/<slug:slug>/enquire/', views.product_enquiry,         name='product_enquiry'),
    path('products/<slug:slug>/add/',     views.cart_add,                name='cart_add'),
    path('cart/',                         views.cart_view,               name='cart'),
    path('cart/<int:item_id>/update/',    views.cart_update,             name='cart_update'),
    path('cart/<int:item_id>/remove/',    views.cart_remove,             name='cart_remove'),
    path('checkout/',                     views.checkout,                name='checkout'),
    path('about/',                        views.about,                   name='about'),
    path('contact/',                      views.contact,                 name='contact'),
    path('book/',                         views.book,                    name='book'),
    path('blog/',                         views.blog,                    name='blog'),
    path('blog/<slug:slug>/',             views.blog_detail,             name='blog_detail'),
    path('subscribe/',                    views.subscribe,               name='subscribe'),
    path('testimonial/submit/',           views.submit_testimonial,      name='submit_testimonial'),
    # Admin extras
    path('admin-tools/calendar/',         views.admin_calendar,          name='admin_calendar'),
    path('admin-tools/wa-templates/',     views.whatsapp_templates,      name='wa_templates'),
    path('admin-tools/receipt/<int:pk>/', views.admin_appointment_pdf,   name='admin_receipt_pdf'),
]
