from django.urls import path
from . import views

app_name = 'scheduling'

urlpatterns = [
    path('',views.scheduling,name='scheduling'),
    path("schedule/", views.scheduling_view, name="schedule"),
    path("update/<int:pk>/", views.update_workorder_date, name="update_workorder_date"),
    path("gantt/<int:week>/<int:garage_id>/", views.gantt_view, name="gantt"),
    path("forecast/", views.forecast_view, name="forecast"),
    path("weeksetup/", views.weeksetup_view, name="weeksetup_view"),
    path("weeksetup/export/", views.export_weeks_excel, name="export_weeks_excel"),
    path("gantt/<int:week>/<int:garage_id>/", views.gantt_view, name="gantt"),
    path('save-working-copy/', views.save_working_copy, name='save_working_copy'),
    path('forecast/export/', views.export_forecast_excel, name='export_forecast_excel'),
    path('shop_plan_view/', views.shop_plan_view, name='shop_plan_view'), 
    path('commit_schedule/', views.commit_schedule, name='commit_schedule'),
]