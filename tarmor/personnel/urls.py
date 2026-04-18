from django.urls import path
from . import views

app_name = 'personnel'

urlpatterns = [
    path('', views.personnel, name='personnel'), 
    
    # Forms and Actions
    path('add_employee/', views.add_employee, name='add_employee'),
    path('edit_employee/', views.edit_employee, name='edit_employee'),
    path('search_employee/', views.search_employee, name='search_employee'),
    path('search_certifications/', views.search_certifications, name='search_certifications'),
    path('export_employees_excel', views.export_employees_excel, name='export_employees_excel'),
    path('export_certs_excel', views.export_certs_excel, name='export_certs_excel'),
    path('crew_calendar/', views.crew_calendar, name='crew_calendar'),
    path('shiftrotation_upload/',views.shiftrotation_upload,name="shiftrotation_upload"),
    path('edit_schedule/', views.edit_schedule, name='edit_schedule'),
    path('edit_schedule/<int:rotation_id>/', views.edit_schedule, name='edit_schedule_with_id'),
]