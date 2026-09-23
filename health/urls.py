from django.urls import path
from . import views

app_name = 'health'

urlpatterns = [
    path('',                      views.index,            name='index'),
    path('anatomy/',              views.anatomy_list,      name='anatomy_list'),
    path('anatomy/<slug:slug>/',  views.anatomy_detail,    name='anatomy_detail'),
    path('conditions/',           views.conditions_list,   name='conditions_list'),
    path('conditions/<slug:slug>/', views.condition_detail, name='condition_detail'),
    path('herbs/',                views.herbs_list,        name='herbs_list'),
    path('herbs/<slug:slug>/',    views.herb_detail,       name='herb_detail'),
    path('wellness/',             views.wellness_list,     name='wellness_list'),
]
