import os
import django

# 1. Manually configure and initialize Django for standalone execution
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tarmor_config.settings')
django.setup()

# 2. Imports must happen AFTER django.setup() is called
from django.contrib.auth.models import User
from django_tenants.utils import schema_context

def run():
    # Provision inside your tenant schema
    with schema_context('test_company_a'):
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@tarmorglobal.com',
                password='YourSecurePassword123!' # <-- Change to your secure password
            )
            print("Superuser successfully created in test_company_a")
        else:
            print("Admin already exists in test_company_a")

    # Safe public schema fallback pass
    try:
        with schema_context('public'):
            if not User.objects.filter(username='global_admin').exists():
                User.objects.create_superuser(
                    username='global_admin',
                    email='master@tarmorglobal.com',
                    password='YourGlobalSecurePassword123!' # <-- Change to your secure password
                )
                print("Superuser successfully created in public schema")
    except Exception as e:
        print(f"Skipping public superuser creation: {e}")

if __name__ == '__main__':
    run()