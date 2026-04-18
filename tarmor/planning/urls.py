from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'planning'

urlpatterns = [
    path('', views.planning, name='planning'),
    path('qm/create/', views.create_qm, name='create_qm'),
    path('qm/edit/', views.edit_qm, name='edit_qm'),
    path('qm/edit/<int:pk>/', views.edit_qm_record, name='edit_qm_record'),
    path('qm/search/', views.search_qm, name='search_qm'),
    path('plan-orders/search/', views.search_plan_orders, name='search_plan_orders'),
    path('plan-orders/export/', views.export_plan_wos_excel, name='export_plan_wos_excel'),
    path('qm/<int:pk>/create-work-order/', views.create_qm_work_order_now, name='create_qm_work_order_now'),
    path('forecast/', views.forecast, name='forecast'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)