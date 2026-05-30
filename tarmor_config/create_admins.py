import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tarmor_config.settings')
django.setup()

from django.contrib.auth import get_user_model
from django_tenants.utils import tenant_context
from customers.models import Company

try:
    User = get_user_model()

    # Fetch all active company records you have generated
    companies = Company.objects.all()

    if not companies.exists():
        print("--- NO COMPANIES FOUND YET TO SEED ADMINS INTO ---")
    else:
        # Loop through every company vault and place your master logins inside them
        for tenant in companies:
            # Skip the public schema since user tables don't live there
            if tenant.schema_name == 'public':
                continue
                
            with tenant_context(tenant):
                # Register Administrator Account 1
                if not User.objects.filter(username='mklatt').exists():
                    User.objects.create_superuser('admin_main', 'mkklatt1@gmail.com', 'Password123!')
                    print(f"--- ADMIN 1 SECURED IN SCHEMA: {tenant.schema_name} ---")
                    
                # Register Administrator Account 2
                if not User.objects.filter(username='jmaber').exists():
                    User.objects.create_superuser('admin_partner', 'joel.maber@gmail.com', 'Password456!')
                    print(f"--- ADMIN 2 SECURED IN SCHEMA: {tenant.schema_name} ---")
                    
except Exception as e:
    print(f"Error seeding admins: {e}")