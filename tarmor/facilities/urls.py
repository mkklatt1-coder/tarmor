from django.urls import path
from . import views

app_name = "facilities"

urlpatterns = [
    path("", views.facilities, name="facilities"),
    path("add-costcentre/", views.costcentre_upload, name="costcentre_upload"),
    path('edit_costcentre/', views.edit_costcentre, name='edit_costcentre'),
    path('edit_costcentre/<int:pk>/', views.edit_costcentre, name='edit_costcentre'),
    path('search_costcentre/', views.search_costcentre, name='search_costcentre'),
    path('export/excel/', views.export_costcentre_excel, name='export_costcentre_excel'),
    path("add-facility/", views.facility_upload, name="facility_upload"),
    path('edit_facility/', views.edit_facility, name='edit_facility'),
    path('edit_facility/<int:pk>/', views.edit_facility, name='edit_facility'),
    path("search_facilities/", views.search_facilities, name="search_facilities"),
]