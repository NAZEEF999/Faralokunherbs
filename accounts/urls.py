from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/',       views.patient_login,          name='login'),
    path('logout/',      views.patient_logout,          name='logout'),
    path('register/',    views.register,                name='register'),
    path('dashboard/',   views.dashboard,               name='dashboard'),
    path('appointments/',views.my_appointments,         name='my_appointments'),
    path('profile/',     views.edit_profile,            name='edit_profile'),
    path('receipt/<int:pk>/pdf/', views.appointment_receipt_pdf, name='receipt_pdf'),
]
