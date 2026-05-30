import os
import django

# Initialize the Django ecosystem environment inside the cloud engine
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tarmor_config.settings')
django.setup()

from django.contrib.auth import get_user_model
from customers.models import Company

try:
    # Target the global tracking schema space
    from django.db import connection
    connection.set_schema_to_public()
    
    User = get_user_model()
    
    # Generate Administrator Account 1
    if not User.objects.filter(username='Ben Magro').exists():
        User.objects.create_superuser('ben_magro', 'bmagro@gmail.com', 'Password123!')
        print("--- ADMIN 1 CREATED SUCCESSFULLY ---")
        
    # Generate Administrator Account 2
    if not User.objects.filter(username='Joel Maber').exists():
        User.objects.create_superuser('joel_maber', 'joel.maber@gmail.com', 'Password456!')
        print("--- ADMIN 2 CREATED SUCCESSFULLY ---")
        
except Exception as e:
    print(f"Error seeding admins: {e}")