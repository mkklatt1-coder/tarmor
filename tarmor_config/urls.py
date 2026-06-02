from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from customers.views import tenant_login_view, trigger_create_users_view

urlpatterns = [
    path('setup-users-secret-abc/', trigger_create_users_view),
    path('admin/', admin.site.urls),
    path('login/', tenant_login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('', include('core.urls')),
    path('equipment/', include('equipment.urls')),
    path('work_orders/', include('work_orders.urls')),
    path('meters/', include('meters.urls')),
    path('personnel/', include('personnel.urls')),
    path("facilities/", include("facilities.urls")),
    path("failures/", include("failures.urls")),
    path("timesheets/", include('timesheets.urls')),
    path("suppliers/", include('suppliers.urls')),
    path("purchasing/", include('purchasing.urls')),
    path("inventory/", include('inventory.urls')),
    path("reliability/", include("reliability.urls")),
    path("kpis/", include("kpis.urls")),
    path("planning/", include("planning.urls")),
    path("scheduling/", include("scheduling.urls")),
    path("condition_monitoring/", include("condition_monitoring.urls")),
    path('chaining/', include('smart_selects.urls')),
    path('moc/', include('moc.urls')),
    path('projects/', include('projects.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)