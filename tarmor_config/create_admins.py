import os
import django

# 1. Manually configure and initialize Django for standalone execution
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tarmor_config.settings')
django.setup()

# 2. Imports must happen AFTER django.setup() is called
from django.contrib.auth.models import User
from django_tenants.utils import schema_context

def run():
    with schema_context('test_company'):
        # 1. Properly Hashed Master Admin
        if not User.objects.filter(username='admin').exists():
            admin_user = User(
                username='admin',
                email='markklatt@tarmorglobal.com',
                is_superuser=True,
                is_staff=True
            )
            admin_user.set_password('Password123!')  # <-- This forces Django to securely hash it
            admin_user.save()
            print("Superuser successfully created and hashed in test_company")
        else:
            # Force update password if the user already exists to fix the old broken/unhashed text string
            admin_user = User.objects.get(username='admin')
            admin_user.set_password('Password123!')
            admin_user.save()

        # 2. Define your 4 additional users
        additional_users = [
            {'username': 'jmaber', 'email': 'joelmaber@tarmorglobal.com', 'password': 'Password123!', 'is_staff': True},
            {'username': 'markklatt', 'email': 'markklatt@tarmorglobal.com', 'password': 'Password123!', 'is_staff': True},
            {'username': 'bmagro', 'email': 'bmagro@gmail.com', 'password': 'Password123!', 'is_staff': False},
            {'username': 'kklatt', 'email': 'mkklatt1@gmail.com', 'password': 'Password123!', 'is_staff': False},
        ]

        # 3. Loop and safely create each user inside the test_company partition
        for user_data in additional_users:
            if not User.objects.filter(username=user_data['username']).exists():
                u = User(
                    username=user_data['username'],
                    email=user_data['email'],
                    is_staff=user_data['is_staff']
                )
                u.set_password(user_data['password'])  # <-- Hashes the password
                u.save()
                print(f"Successfully created and hashed user: {user_data['username']}")
            else:
                # Force update existing users to fix their plain text passwords
                u = User.objects.get(username=user_data['username'])
                u.set_password(user_data['password'])
                u.save()
                print(f"Password fixed for existing user: {user_data['username']}")

    # Safe public schema fallback pass
    try:
        with schema_context('public'):
            if not User.objects.filter(username='admin').exists():
                admin_user = User(
                    username='admin',
                    email='markklatt@tarmorglobal.com',
                    is_superuser=True,
                    is_staff=True
                )
                admin_user.set_password('Password123!')  # <-- This forces Django to securely hash it
                admin_user.save()
                print("Superuser successfully created and hashed in test_company")
            else:
                # Force update password if the user already exists to fix the old broken/unhashed text string
                admin_user = User.objects.get(username='admin')
                admin_user.set_password('Password123!')
                admin_user.save()
    except Exception as e:
        print(f"Skipping public superuser creation: {e}")

if __name__ == '__main__':
    run()