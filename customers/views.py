from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.db import connection
from django_tenants.utils import get_tenant_model

def tenant_login_view(request):
    error_message = None
    
    if request.method == 'POST':
        # 1. Grab inputs from the updated login.html form
        company_slug = request.POST.get('company_slug', '').strip().lower()
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        Tenant = get_tenant_model()
        
        # 2. Force database context to 'public' to locate the company tenant record
        connection.set_schema_to_public()
        try:
            tenant = Tenant.objects.get(schema_name=company_slug)
        except Tenant.DoesNotExist:
            error_message = "Invalid company organization code."
            return render(request, 'registration/login.html', {'error_message': error_message})
            
        # 3. Temporarily point the database thread to that company's private schema to check user login credentials
        connection.set_schema(tenant.schema_name, include_public=True)
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # 4. SUCCESS! Store the selected company identifier inside the browser session cookie
            request.session['tenant_schema'] = tenant.schema_name
            login(request, user)
            return redirect('home')  # Points to the dashboard root mapped in core.urls
        else:
            error_message = "Invalid user login ID or password for this company."
            
    return render(request, 'registration/login.html', {'error_message': error_message})