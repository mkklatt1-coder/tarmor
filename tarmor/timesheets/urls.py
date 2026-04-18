from django.urls import path
from . import views

app_name = 'timesheets'

urlpatterns = [
    path('', views.timesheets, name='timesheets'), 
    path('add_timesheet/', views.add_timesheet, name='add_timesheet'),
    path('edit/', views.edit_timesheet, name='edit_timesheet'),
    path('search/', views.search_timesheets, name='search_timesheets'),
]