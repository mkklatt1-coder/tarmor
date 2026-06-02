from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.db import connection
from django_tenants.utils import get_tenant_model

def tenant_login_view(request):
    error_message = None
    
    if request.method == 'POST':
        company_slug = request.POST.get('company_slug', '').strip().lower()
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        Tenant = get_tenant_model()
        
        connection.set_schema_to_public()
        try:
            tenant = Tenant.objects.get(schema_name=company_slug)
        except Tenant.DoesNotExist:
            error_message = "Invalid Company Code."
            return render(request, 'registration/login.html', {'error_message': error_message})
            
        connection.set_schema(tenant.schema_name, include_public=True)
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            request.session['tenant_schema'] = tenant.schema_name
            login(request, user)
            return redirect('home')
        else:
            error_message = "Invalid User Login ID or Password for this organization."
            
    return render(request, 'registration/login.html', {'error_message': error_message})