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
    with schema_context('test_company'):
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='markklatt@tarmorglobal.com',
                password='Password123!' # <-- Change to your secure password
            )
            print("Superuser successfully created in test_company")
        else:
            print("Admin already exists in test_company")

        additional_users = [
            {'jmaber': 'jmaber', 'joelmaber@tarmorglobal.com': 'user1@tarmorglobal.com', 'password': 'Password123!', 'is_staff': True},
            {'mklatt': 'mklatt', 'email': 'markklatt@tarmorglobal.com', 'password': 'Password123!', 'is_staff': True},
            {'kklatt': 'kklatt', 'email': 'mkklatt1@gmail.com', 'password': 'Password123!', 'is_staff': False},
            {'bmagro': 'bmagro', 'email': 'bmagro@gmail.com', 'password': 'Password123!', 'is_staff': False},
        ]

        # 3. Loop and safely create each user inside the test_company partition
        for user_data in additional_users:
            if not User.objects.filter(username=user_data['username']).exists():
                User.objects.create_user(
                    username=user_data['username'],
                    email=user_data['email'],
                    password=user_data['password'],
                    is_staff=user_data['is_staff'] # Grants access to django backend panel if True
                )
                print(f"Successfully created user: {user_data['username']}")
            else:
                print(f"User {user_data['username']} already exists. Skipping.")

    # Safe public schema fallback pass
    try:
        with schema_context('public'):
            if not User.objects.filter(username='admin').exists():
                User.objects.create_superuser(
                    username='admin',
                    email='markklatt@tarmorglobal.com',
                    password='Password123!' # <-- Change to your secure password
                )
                print("Superuser successfully created in public schema")
    except Exception as e:
        print(f"Skipping public superuser creation: {e}")

if __name__ == '__main__':
    run()