from django.urls import path
from . import views

app_name = 'equipment'

urlpatterns = [
    # Main Workspace
    path('', views.equipment, name='equipment'), 
    
    # Forms and Actions
    path('upload/', views.equpload, name='equpload'),
    path('search/', views.search_eq, name='search_eq'),
    path('edit/', views.edit_eq, name='edit_eq'),
    path('add_component/', views.add_component, name='add_component'),
    path('shift_report/', views.shift_report, name='shift_report'),
    
    # Data & AJAX helpers
    path('equipment:export/', views.export_equipment, name='export'),
    path('ajax/load-types/', views.load_equipment_types, name='ajax_load_types'),
    path('ajax/generate-id/', views.generate_eq_number, name='ajax_generate_id'),
    path('get-equipment-details/', views.get_equipment_details, name='get_equipment_details'),
    path('get-next-component-id/', views.get_next_component_id, name='get_next_component_id'),
    
    path('change_component/', views.change_component, name='change_component'),
    path('get-equipment-components/', views.get_equipment_components, name='get_equipment_components'),
    path('get-component-details-by-id/', views.get_component_details_by_id, name='get_component_details_by_id'),
    path('search_component_history/', views.search_component_history, name = 'search_component_history'),
    path('export/', views.export_component_history, name='export'),
    path('shift_report/', views.shift_report, name='shift_report'),
    path('shift_report/<int:pk>/', views.shift_report_edit, name='shift_report_edit'),
    path('shift_report/excel/<int:report_id>/', views.export_shift_report_excel, name='export_shift_report_excel'),
    path('shift_report/archive/excel/', views.export_shift_archive_excel, name='export_shift_archive_excel'),
    path('search_comp_list/', views.search_comp_list, name='search_comp_list'),
    path('export_list_excel/', views.export_list_excel, name='export_list_excel'),
    path('ajax/load-options/', views.load_equipment_options, name='load_options'),
]