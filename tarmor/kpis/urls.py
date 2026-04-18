from django.urls import path
from . import views

app_name = 'kpis'

urlpatterns = [
    path('', views.kpis, name='kpis'),
    path('top_failures/', views.TopFailuresView.as_view(), name='top_failures'),
    path('export_top_failures_excel/', views.export_top_failures_excel, name='export_top_failures_excel'),
    path('failure_frequency/', views.failure_frequency_report, name='failure_frequency_report'),
    path('failure_frequency_chart/', views.failure_frequency_chart, name='failure_frequency_chart'),
    path('export_failure_frequency_excel/', views.export_failure_frequency_excel, name='export_failure_frequency_excel'),
    path('mtbf/', views.mtbf_report, name='mtbf_report'),
    path('export_mtbf_excel/', views.export_mtbf_excel, name='export_mtbf_excel'),
    path('mttr/', views.mttr_report, name='mttr_report'),
    path('export_mttr_excel/', views.export_mttr_excel, name='export_mttr_excel'),
    path('availability_utilisation_report/', views.availability_utilisation_report, name='availability_utilisation_report'),
    path('export_au_excel/', views.export_au_excel, name='export_au_excel'),
]