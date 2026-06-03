from django.db import connection
from django_tenants.utils import get_tenant_model

class SessionTenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    def __call__(self, request):
        path = request.path_info
        if path.startswith('/static/') or path.startswith('/media/') or 'favicon.ico' in path:
            return self.get_response(request)
        schema_name = 'public'
        if hasattr(request, 'session') and 'tenant_schema' in request.session:
            schema_name = request.session['tenant_schema']
        Tenant = get_tenant_model()
        try:
            tenant = Tenant.objects.get(schema_name=schema_name)
        except Tenant.DoesNotExist:
            tenant = Tenant.objects.get(schema_name='public')
            connection.set_schema_to_public()
        else:
            request.tenant = tenant
            connection.set_tenant(tenant)
        request.tenant = tenant
        return self.get_response(request)