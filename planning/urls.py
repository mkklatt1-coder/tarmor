from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'planning'

urlpatterns = [
    path('', views.planning, name='planning'),

    path('qm/create/', views.create_qm, name='create_qm'),
    path('qm/lookup/', views.lookup_qm_for_edit, name='lookup_qm_for_edit'),
    path('qm/edit/<int:pk>/', views.edit_qm_record, name='edit_qm_record'),
    path('qm/search/', views.search_qm, name='search_qm'),
    path('plan-orders/search/', views.search_plan_orders, name='search_plan_orders'),
    path('plan-orders/export/', views.export_plan_wos_excel, name='export_plan_wos_excel'),
    path('qm/<int:pk>/create-work-order/', views.create_qm_work_order_now, name='create_qm_work_order_now'),
    path('forecast/', views.forecast_dashboard, name='forecast'),
    path('create_plan/', views.create_plan, name='create_plan'),
    path('edit_plan/', views.edit_plan, name='edit_plan'),
    path('plan/edit/<int:pk>/', views.edit_plan, name='edit_plan'),
    path('search_plans/', views.search_plans, name='search_plans'),
    path('get-linked-meters/', views.get_linked_meters, name='get_linked_meters'),
    path('plans/export/', views.export_plans_excel, name='export_plans_excel'),
    path('qm/export/', views.export_qm_excel, name='export_qm_excel'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
