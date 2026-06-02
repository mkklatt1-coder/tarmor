import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tarmor_config.settings')
django.setup()

from django.contrib.auth import get_user_model
from django_tenants.utils import tenant_context
from customers.models import Company, CompanyDomain

try:
    if not Company.objects.filter(schema_name='public').exists():
        public_tenant = Company(schema_name='public', name='TARMOR Master Live System')
        public_tenant.save()
        print("--- MASTER LIVE PUBLIC SCHEMA CREATED ---")
        
        public_domain = CompanyDomain(domain='app.tarmorglobal.com', tenant=public_tenant, is_primary=True)
        public_domain.save()
        print(f"--- ROOT DOMAIN DETECTED AND EXTENDED TO PUBLIC SCHEMA ---")

    User = get_user_model()
    companies = Company.objects.all()

    for tenant in companies:
        if tenant.schema_name == 'public':
            continue
            
        if not User.objects.filter(username='jmaber').exists():
                    User.objects.create_superuser('jmaber', 'joel.maber@gmail.com', 'Password123!')
                    print(f"--- USER jmaber SECURED IN LIVE SCHEMA: {tenant.schema_name} ---")
                    
        if not User.objects.filter(username='bmagro').exists():
            User.objects.create_superuser('bmagro', 'bmagro@gmail.com', 'Password456!')
            print(f"--- USER bmagro SECURED IN LIVE SCHEMA: {tenant.schema_name} ---")
                
except Exception as e:
    print(f"Error executing cloud seed script: {e}")