from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.inventory, name='inventory'), 
    path('add_inventory_item/', views.add_inventory_item, name='add_inventory_item'),
    path('edit_inventory_item/', views.edit_inventory_item, name='edit_inventory_item'),
    path('delete_inventory_group/<int:pk>/', views.delete_inventory_group, name='delete_inventory_group'),
    path('search_inventory/', views.search_inventory, name='search_inventory'),
    path('export_inventory_excel/', views.export_inventory_excel, name='export_inventory_excel'),
    path('manage_inventory/', views.manage_inventory, name='manage_inventory'),
    path('export_manage_inventory_excel/', views.export_manage_inventory_excel, name='export_manage_inventory_excel'),
]