from django.urls import path
from . import views

app_name = 'work_orders'

urlpatterns = [
    path("", views.work_orders, name='work_orders'),
    path('add_work_order/', views.add_work_order, name='add_work_order'),
    path('edit_work_order/', views.edit_work_order, name='edit_work_order'),
    path('edit_work_order/<int:pk>/', views.edit_work_order, name='edit_work_order'),
    path('equipment_lookup/', views.equipment_lookup, name='equipment_lookup'),
    path('search_work_orders/', views.search_work_orders, name='search_work_orders'),
    path('export_wos_excel/', views.export_wos_excel, name='export_wos_excel'),
    path('print_work_order/<int:pk>/', views.fill_pdf, name='print_work_order'),
    path('load_components/', views.load_components, name='load_components'),
]