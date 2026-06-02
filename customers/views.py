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
            error_message = "Invalid company organization code."
            return render(request, 'registration/login.html', {'error_message': error_message})
            
        request.tenant = tenant
        connection.set_tenant(request.tenant)
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            request.session['tenant_schema'] = tenant.schema_name
            login(request, user)
            return redirect('home')
        else:
            connection.set_schema_to_public()
            error_message = "Invalid user login ID or password for this company."
            
    return render(request, 'registration/login.html', {'error_message': error_message})