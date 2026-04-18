from django.urls import path
from . import views

app_name = 'scheduling'

urlpatterns = [
    path('',views.scheduling,name='scheduling'),
    path("schedule/", views.scheduling_view, name="schedule"),
    path("update/<int:pk>/", views.update_workorder_date, name="update_workorder_date"),
    path("lock/<int:schedule_id>/", views.lock_schedule, name="lock_schedule"),

]