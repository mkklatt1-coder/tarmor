import os
import csv
import django

# 1. Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tarmor_config.settings')
django.setup()

from equipment.models import EQ_Type, AssetType  # Ensure this matches your model name

def run():
    file_path = 'eq_types.csv' 
    
    with open(file_path, mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            asset_obj, _ = AssetType.objects.get_or_create(name=row['Asset_Type'])

            # Change the lookup to use BOTH fields
            obj, created = EQ_Type.objects.update_or_create(
                Equipment_Type=row['Equipment_Type'], 
                Asset_Type=asset_obj, # Adding this to the lookup criteria
                defaults={
                    'Prefix': row['Prefix'],
                }
            )
            
            status = "Created" if created else "Updated"
            print(f"{status}: {obj.Equipment_Type} ({asset_obj.name})")
    
if __name__ == "__main__":
    run()