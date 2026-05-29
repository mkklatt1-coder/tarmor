from django.urls import path
from . import views

app_name = 'meters'

urlpatterns = [
      
    # Main Workspace
    path('', views.meters, name='meters'),
    
    # Forms and Actions
    path('new_reading/', views.new_reading, name='new_reading'),
    path('edit_reading/', views.edit_reading, name='edit_reading'),
    path('search/', views.search_readings, name='search_readings'),
    path('export/', views.export_readings_excel, name='export'),
    path('mass_upload/', views.mass_upload_readings, name='mass_upload'),
    path('download-template/', views.download_meter_template, name='download_template'),
]