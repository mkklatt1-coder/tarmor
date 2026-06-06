from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import update_last_login
from django.contrib.auth.signals import user_logged_in
from django.db import connection
from django_tenants.utils import get_tenant_model, schema_context
from django.http import HttpResponse
import traceback
from django.utils import timezone
from tarmor_config.create_admins import run as run_create_admins
from django.contrib.auth import logout

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
            user = authenticate(
                request=request,
                username=username,
                password=password,
            )
        if user is not None:
            import traceback
            try:
                connection.set_schema_to_public()
                user_logged_in.disconnect(
                    update_last_login,
                    dispatch_uid="update_last_login",
                )
                try:
                    login(request, user)
                finally:
                    user_logged_in.connect(
                        update_last_login,
                        dispatch_uid="update_last_login",
                    )
                request.session['tenant_schema'] = tenant.schema_name
                request.session.save()
                with schema_context(tenant.schema_name):
                    user.last_login = timezone.now()
                    user.save(update_fields=['last_login'])
                return redirect('core:home')
            except Exception as e:
                traceback.print_exc()
                raise
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
    
def tenant_logout_view(request):
    try:
        connection.set_schema_to_public()
        logout(request)
        return redirect("login")
    except Exception as e:
        traceback.print_exc()
        return HttpResponse(f"Logout failed: {e}", status=500)