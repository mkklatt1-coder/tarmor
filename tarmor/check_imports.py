import os
import sys

apps = [
    'django_filters', 'import_export', 'phonenumber_field', 
    'barcode', 'holidays', 'rest_framework', 'crispy_forms'
]

for app in apps:
    try:
        __import__(app)
        print(f"✅ {app} is installed")
    except ImportError:
        print(f"❌ {app} is MISSING")