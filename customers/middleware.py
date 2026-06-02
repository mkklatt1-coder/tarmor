from django.db import connection
from django_tenants.utils import get_tenant_model

class SessionTenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        schema_name = 'public'
        
        if hasattr(request, 'session') and 'tenant_schema' in request.session:
            schema_name = request.session['tenant_schema']
            
        Tenant = get_tenant_model()
        try:
            tenant = Tenant.objects.get(schema_name=schema_name)
            request.tenant = tenant
            
            connection.set_schema(tenant.schema_name, include_public=True)
            
        except Tenant.DoesNotExist:
            request.tenant = Tenant.objects.get(schema_name='public')
            connection.set_schema_to_public()

        return self.get_response(request)