from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.db import connection
from django_tenants.utils import get_tenant_model, schema_context
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
            
        with schema_context(tenant.schema_name):
            user = authenticate(request=request, username=username, password=password)
            
            if user is not None:
                request.session['tenant_schema'] = tenant.schema_name
                login(request, user)
                request.session.save() 
                return redirect('home')
            else:
                error_message = "Invalid User Login ID or Password for this organization."
                return render(request, 'registration/login.html', {'error_message': error_message})
            
    return render(request, 'registration/login.html', {'error_message': error_message})

def trigger_create_users_view(request):
    try:
        run_create_admins()
        
        with schema_context('test_company'):
            user = authenticate(username='admin', password='Password123!') 
            
            if user is not None:
                return HttpResponse("<h1>Internal Auth Test: SUCCESS! User found and authenticated inside test_company.</h1>")
            else:
                return HttpResponse("<h1>Internal Auth Test: FAILED. Script ran, but Django cannot authenticate the user inside test_company.</h1>")
                
    except Exception as e:
        return HttpResponse(f"<h1>Error running script or test: {str(e)}</h1>")