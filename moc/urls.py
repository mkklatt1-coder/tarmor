from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'moc'

urlpatterns = [
    path('', views.mocs, name='mocs'),
    path('add_moc/', views.add_moc_view, name='add_moc'),
    path('edit/', views.edit_moc_view, name='edit_moc_base'),
    path('edit/<str:moc_number>/', views.edit_moc_view, name='edit_moc'),
    path('edit/<str:moc_number>/section/<str:section>/', views.moc_questions_response, name='moc_question_resp'),
    path("api/<str:moc_number>/effval/", views.moc_effval_api, name="moc_effval_api"),
    path('moc_questions/', views.moc_questions, name='moc_questions'),
    path("<str:moc_number>/safety-health/",views.safety_health_view,name="safety_health"),
    path('upload/<str:moc_number>/', views.upload_attachment_api, name='upload_attachment_api'),
    path('search_mocs/', views.moc_search_list, name='search_mocs'),
    path('moc_dashboard/', views.moc_dashboard, name='moc_dashboard'),
    path('export/rankings/', views.export_moc_rankings_excel, name='export_rankings'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)