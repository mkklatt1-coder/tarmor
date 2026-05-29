from django.urls import path
from . import views

app_name = 'reliability'

urlpatterns = [
    path('', views.reliability, name='reliability'),
    path('lifecycle-plan/', views.rebuild_replacement_plan, name='rebuild_plan'),
    path('ajax/filter-eq-types/', views.filter_eq_types, name='filter_eq_types'),
    path('ajax/filter-eq-numbers/', views.filter_eq_numbers, name='filter_eq_numbers'),
    
]