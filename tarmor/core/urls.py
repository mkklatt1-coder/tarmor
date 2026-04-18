from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # This matches the empty string from the main config
    path('', views.home, name='home'), 
]