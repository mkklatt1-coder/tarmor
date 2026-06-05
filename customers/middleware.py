from django.db import connection
from django.shortcuts import redirect
from django_tenants.utils import get_tenant_model
from django.db import connection
from django.shortcuts import redirect
from django_tenants.utils import get_tenant_model

class SessionTenantMiddleware:
    PUBLIC_PATH_PREFIXES = (
        "/static/",
        "/media/",
        "/accounts/login/",
        "/accounts/logout/",
        "/admin/login/",
    )
    PUBLIC_EXACT_PATHS = (
        "/favicon.ico",
    )
    def __init__(self, get_response):
        self.get_response = get_response
    def __call__(self, request):
        path = request.path_info
        try:
            if self._is_public_path(path):
                connection.set_schema_to_public()
                request.tenant = self._get_public_tenant()
                return self.get_response(request)
            return self._handle_tenant_request(request)
        finally:
            connection.set_schema_to_public()
    def _handle_tenant_request(self, request):
        schema_name = request.session.get("tenant_schema")
        if not schema_name or schema_name == "public":
            request.session.pop("tenant_schema", None)
            connection.set_schema_to_public()
            request.tenant = self._get_public_tenant()
            return redirect("login")
        Tenant = get_tenant_model()
        try:
            tenant = Tenant.objects.get(schema_name=schema_name)
        except Tenant.DoesNotExist:
            request.session.pop("tenant_schema", None)
            connection.set_schema_to_public()
            request.tenant = self._get_public_tenant()
            return redirect("login")
        request.tenant = tenant
        connection.set_tenant(tenant)
        return self.get_response(request)
    def _is_public_path(self, path):
        if path in self.PUBLIC_EXACT_PATHS:
            return True
        return any(path.startswith(prefix) for prefix in self.PUBLIC_PATH_PREFIXES)
    def _get_public_tenant(self):
        Tenant = get_tenant_model()
        return Tenant.objects.get(schema_name="public")