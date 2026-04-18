import csv
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tarmor.settings')
django.setup()

from equipment.models import Equipment, AssetType

def upload_equipment(file_path):
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Get or create the AssetType first so the Foreign Key exists
            a_type, _ = AssetType.objects.get_or_create(name=row['asset_type'])
            
            Equipment.objects.get_or_create(
                Asset_Type=row['number'],
                Equpipment_Type=row['description'],
                Prefix=a_type
            )
    print("Upload Complete!")