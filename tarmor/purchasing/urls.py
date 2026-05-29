from django.urls import path
from . import views

app_name = 'purchasing'

urlpatterns = [
    path('', views.purchasing, name='purchasing'), 
    path('purchases/', views.purchases, name='purchases'),
    path('create/', views.create_purchase, name='create_purchase'),
    path('edit/', views.edit_purchase, name='edit_purchase'),
    path('edit/<int:pk>/', views.edit_purchase, name='edit_purchase_loaded'),
    path('search-load/', views.search_purchase_load, name='search_purchase_load'),
    path('print/<int:pk>/', views.print_purchase_pdf, name='print_purchase_pdf'),
    path('ajax/purchase-number-preview/', views.purchase_number_preview, name='purchase_number_preview'),
    path('ajax/wo-cc-options/', views.get_wo_cc_options, name='get_wo_cc_options'),
    path('ajax/part-details/', views.get_part_details, name='get_part_details'),
    path('ajax/purchase-search-options/', views.purchase_search_options, name='purchase_search_options'),
    path('search/', views.search_purchases, name='search_purchases'),
    path('export/', views.export_purchases_excel, name='export_purchases'),
    path('get_part_options/', views.get_part_options, name='get_part_options'),
]