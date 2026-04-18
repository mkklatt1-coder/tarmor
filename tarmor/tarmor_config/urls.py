from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
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
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)