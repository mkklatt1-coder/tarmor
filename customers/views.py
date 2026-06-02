from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.db import connection
from django_tenants.utils import get_tenant_model
from django.http import HttpResponse
from tarmor_config.create_admins import run as run_create_admins

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
            
            request.session.modified = True
            return redirect('home')
        else:
            error_message = "Invalid User Login ID or Password for this organization."
            
    return render(request, 'registration/login.html', {'error_message': error_message})

def trigger_create_users_view(request):
    try:
        run_create_admins()
        return HttpResponse("<h1>Success! All users created in the database.</h1>")
    except Exception as e:
        return HttpResponse(f"<h1>Error running script: {str(e)}</h1>")