from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django_tenants.utils import schema_context

class Command(BaseCommand):
    help = 'Safely provisions superuser accounts across public and tenant schemas'

    def handle(self, *args, **options):
        with schema_context('test_company_a'):
            if not User.objects.filter(username='admin').exists():
                User.objects.create_superuser(
                    username='admin',
                    email='markklatt@tarmorglobal.com',
                    password='Password123!'
                )
                self.stdout.write(self.style.SUCCESS("Superuser created in test_company_a"))
            else:
                self.stdout.write("Admin already exists in test_company_a")

        try:
            with schema_context('public'):
                if not User.objects.filter(username='admin').exists():
                    User.objects.create_superuser(
                        username='admin',
                        email='markklatt@tarmorglobal.com',
                        password='Password123!'
                    )
                    self.stdout.write(self.style.SUCCESS("Superuser created in public"))
        except Exception:
            self.stdout.write("Skipping public superuser creation (auth tables are tenant-only).")