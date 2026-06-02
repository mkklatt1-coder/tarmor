from django.db import connection
from django_tenants.utils import get_tenant_model

class SessionTenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        schema_name = 'public'
        
        if 'tenant_schema' in request.session:
            schema_name = request.session['tenant_schema']
            
        Tenant = get_tenant_model()
        try:
            tenant = Tenant.objects.get(schema_name=schema_name)
            request.tenant = tenant
            connection.set_tenant(request.tenant)
        except Tenant.DoesNotExist:
            request.tenant = Tenant.objects.get(schema_name='public')
            connection.set_tenant(request.tenant)

        return self.get_response(request)