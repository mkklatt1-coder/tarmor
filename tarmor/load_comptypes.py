import os
import csv
import django

# 1. Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tarmor_config.settings')
django.setup()

from equipment.models import ComponentType, AssetType 

def run():
    file_path = 'comptypes.csv' 
    
    with open(file_path, mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                a_type = AssetType.objects.get(name=row['asset_type'])

                # This is the line that's crashing
                obj, created = ComponentType.objects.update_or_create(
                    short_code=row['short_code'],
                    asset_type=a_type,
                    defaults={'name': row['name']}
                )
                
                status = "Created" if created else "Updated"
                print(f"{status}: {obj.name} ({a_type.name})")

            except django.db.utils.IntegrityError:
                # This catches the duplicate and moves to the next line
                print(f"⚠️  DUPLICATE SKIPPED: '{row['name']}' already exists for {row['asset_type']}")
                continue 

            except AssetType.DoesNotExist:
                print(f"❌ ASSET NOT FOUND: '{row['asset_type']}'")
                continue

    print("\n--- Load Finished ---")

if __name__ == "__main__":
    run()