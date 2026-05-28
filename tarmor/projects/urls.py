from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.projects, name='projects'), 
    path('create_project/', views.create_project, name='create_project'),
    path('edit_project/', views.edit_project, name='edit_project'),
    path('edit/<int:pk>/', views.edit_project, name='edit_project_id'),
    path('attachment/add/<int:project_id>/', views.add_attachment, name='add_attachment'),
    path('notes/<int:project_id>/', views.project_notes, name='project_notes'),
    path('lessons/<int:project_id>/', views.project_lessons, name='project_lessons'),
    path('financials/<int:project_id>/', views.project_financials, name='project_financials'),
    path('gantt/<int:project_id>/', views.project_gantt, name='project_gantt'),
    path('tasks/<int:project_id>/', views.project_tasks, name='project_tasks'),
    path('search_projects/', views.search_projects, name='search_projects'),
    path('dashboard/', views.project_dashboard, name='dashboard'),
    path('planning/', views.project_planning, name='project_planning'),

]