from django.urls import path
from . import views

app_name = 'kpis'

urlpatterns = [
    path('', views.kpis, name='kpis'),
    path('top-failures/', views.top_failures_report, name='top_failures'),
    path('export_top_failures_excel/', views.export_top_failures_excel, name='export_top_failures_excel'),
    path('failure_frequency/', views.failure_frequency_report, name='failure_frequency_report'),
    path('failure_frequency_chart/', views.failure_frequency_chart, name='failure_frequency_chart'),
    path('export_failure_frequency_excel/', views.export_failure_frequency_excel, name='export_failure_frequency_excel'),
    path('get-freq-linked-eq-types/', views.get_freq_linked_eq_types, name='get_freq_linked_eq_types'),
    path('mtbf/', views.mtbf_report, name='mtbf_report'),
    path('export_mtbf_excel/', views.export_mtbf_excel, name='export_mtbf_excel'),
    path('get-mtbf-linked-eq-types/', views.get_mtbf_linked_eq_types, name='get_mtbf_linked_eq_types'),
    path('mttr/', views.mttr_report, name='mttr_report'),
    path('export_mttr_excel/', views.export_mttr_excel, name='export_mttr_excel'),
    path('get-mttr-linked-eq-types/', views.get_mttr_linked_eq_types, name='get_mttr_linked_eq_types'),
    path('availability_utilisation_report/', views.availability_utilisation_report, name='availability_utilisation_report'),
    path('export_au_excel/', views.export_au_excel, name='export_au_excel'),
    path('get-kpi-linked-eq-types/', views.get_kpi_linked_eq_types, name='get_kpi_linked_eq_types'),
    path('schedule_compliance_report/', views.schedule_compliance_report, name='schedule_compliance_report'),
    path('export_compliance_excel/', views.export_compliance_excel, name='export_compliance_excel'),
    path('get-compliance-linked-eq-types/', views.get_compliance_linked_eq_types, name='get_compliance_linked_eq_types'),
    path('resource_utilisation_report/', views.resource_utilisation_report, name='resource_utilisation_report'),
    path('export_res_util_excel/', views.export_res_util_excel, name='export_res_util_excel'), 
    path('cost_per_hour_report/', views.cost_per_hour_report, name='cost_per_hour_report'),
    path('export_cost_report_excel/', views.export_cost_report_excel, name='export_cost_report_excel'), 

]