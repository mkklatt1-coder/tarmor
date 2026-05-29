from django.urls import path
from . import views

app_name = 'suppliers'

urlpatterns = [
    path('', views.suppliers, name='suppliers'), 
    path('add_supplier/', views.add_supplier, name='add_supplier'), 
    path('edit_supplier/', views.edit_supplier, name='edit_supplier'), 
    path('search_suppliers/', views.search_suppliers, name='search_suppliers'),
    path('export_suppliers_excel/', views.export_suppliers_excel, name='export_suppliers_excel'),
]