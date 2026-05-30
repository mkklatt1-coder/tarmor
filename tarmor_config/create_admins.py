import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tarmor_config.settings')
django.setup()

from django.contrib.auth import get_user_model
from django_tenants.utils import tenant_context
from customers.models import Company, CompanyDomain

try:
    # --- AUTOMATED MASTER SCHEMA INITIALIZATION ---
    # Check if the core global system structure exists yet
    if not Company.objects.filter(schema_name='public').exists():
        public_tenant = Company(schema_name='public', name='TARMOR Master Live System')
        public_tenant.save()
        print("--- MASTER LIVE PUBLIC SCHEMA CREATED ---")
        
        # LINK YOUR EXACT purchased Wix domain address right here
        # Replace 'yourwixdomain.com' with your actual company URL string
        public_domain = CompanyDomain(domain='tarmorglobal.com', tenant=public_tenant, is_primary=True)
        public_domain.save()
        print(f"--- ROOT DOMAIN DETECTED AND EXTENDED TO PUBLIC SCHEMA ---")

    # --- AUTOMATED ADMINISTRATOR ACCOUNT INJECTION LOOP ---
    User = get_user_model()
    companies = Company.objects.all()

    for tenant in companies:
        # Skip the public schema layout space since auth tables don't reside there
        if tenant.schema_name == 'public':
            continue
            
        with tenant_context(tenant):
            # Verify and register Administrator Account 1
            if not User.objects.filter(username='mklatt').exists():
                User.objects.create_superuser('admin_main', 'mkklatt1@gmail.com', 'Password123!')
                print(f"--- ADMIN 1 SECURED IN LIVE SCHEMA: {tenant.schema_name} ---")
                
            # Verify and register Administrator Account 2
            if not User.objects.filter(username='jmaber').exists():
                User.objects.create_superuser('admin_partner', 'joel.maber@gmail.com', 'Password456!')
                print(f"--- ADMIN 2 SECURED IN LIVE SCHEMA: {tenant.schema_name} ---")
                
except Exception as e:
    print(f"Error executing cloud seed script: {e}")