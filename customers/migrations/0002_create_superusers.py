from django.db import migrations
from django_tenants.utils import schema_context

def create_tenant_and_public_superusers(apps, schema_editor):
    # Grab the active User model securely within migrations
    User = apps.get_model('auth', 'User')

    # 1. Inject the Master Admin account into your new client portal
    with schema_context('test_company_a'):
        if not User.objects.filter(username='mklatt').exists():
            User.objects.create_superuser(
                username='mklatt',
                email='markklatt@tarmorglobal.com',
                password='RedneckU#101'  # <-- Change this to your password
            )

    # 2. Inject a fallback Global Admin into the root public portal
    with schema_context('public'):
        if not User.objects.filter(username='mklatt').exists():
            User.objects.create_superuser(
                username='mklatt',
                email='markklatt@tarmorglobal.com',
                password='Password123!'  # <-- Change this to your password
            )

def rollback_superusers(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    
    with schema_context('test_company_a'):
        User.objects.filter(username='mklatt').delete()
        
    with schema_context('public'):
        User.objects.filter(username='mklatt').delete()

class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0001_initial'), 
    ]

    operations = [
        migrations.RunPython(create_tenant_and_public_superusers, reverse_code=rollback_superusers),
    ]