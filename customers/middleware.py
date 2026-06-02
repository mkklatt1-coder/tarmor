from django.db import connection
from django_tenants.utils import get_tenant_model, schema_context

class SessionTenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. Default to public schema
        schema_name = 'public'
        
        # 2. Check if a company schema is saved in the user's active browser session
        if 'tenant_schema' in request.session:
            schema_name = request.session['tenant_schema']
            
        # 3. Dynamically set the database routing connection
        Tenant = get_tenant_model()
        try:
            tenant = Tenant.objects.get(schema_name=schema_name)
            request.tenant = tenant
            connection.set_tenant(request.tenant)
        except Tenant.DoesNotExist:
            # Fall back safely to public if something is wrong
            request.tenant = Tenant.objects.get(schema_name='public')
            connection.set_tenant(request.tenant)

        response = self.get_response(request)
        return response