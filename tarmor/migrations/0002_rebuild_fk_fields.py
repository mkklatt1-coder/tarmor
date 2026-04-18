from django.db import migrations, models

def convert_data(apps, schema_editor):
    Equipment = apps.get_model('tarmor', 'Equipment')
    EQType = apps.get_model('tarmor', 'EQ_Type')
    AssetType = apps.get_model('tarmor', 'AssetType')
    # -----------------------------
    # 1. Build AssetType map
    # -----------------------------
    existing_assets = Equipment.objects.values_list('Asset_Type', flat=True).distinct()
    asset_map = {}
    for name in existing_assets:
        if not name:
            continue
        obj, created = AssetType.objects.get_or_create(name=name)
        asset_map[name] = obj.id
    # -----------------------------
    # 2. Convert EQ_Type.Asset_Type TEXT → FK
    # -----------------------------
    for eqt in EQType.objects.all():
        old_asset = eqt.Asset_Type
        eqt.Asset_Type_id = asset_map.get(old_asset)
        eqt.save()
    # -----------------------------
    # 3. Build EQ_Type lookup
    # -----------------------------
    eqtype_lookup = {}
    for t in EQType.objects.all():
        key = (t.Asset_Type_id, t.Equipment_Type)
        eqtype_lookup[key] = t.id
    # -----------------------------
    # 4. Convert Equipment.Equipment_Type TEXT → FK
    # -----------------------------
    for eq in Equipment.objects.all():
        key = (eq.Asset_Type_id, eq.Equipment_Type)
        if key not in eqtype_lookup:
            new = EQType.objects.create(
                Asset_Type_id=eq.Asset_Type_id,
                Equipment_Type=eq.Equipment_Type,
                Prefix="UNK"
            )
            eqtype_lookup[key] = new.id
        eq.Equipment_Type_id = eqtype_lookup[key]
        eq.save()
class Migration(migrations.Migration):
    dependencies = [
        ('tarmor', '0001_initial'),
    ]
    operations = [
        # Convert EQ_Type.Asset_Type TEXT → FK
        migrations.AlterField(
            model_name='eq_type',
            name='Asset_Type',
            field=models.ForeignKey(
                to='tarmor.AssetType',
                related_name='equipment_types',
                on_delete=models.CASCADE,
            )
        ),
        # Convert Equipment.Equipment_Type TEXT → FK
        migrations.AlterField(
            model_name='equipment',
            name='Equipment_Type',
            field=models.ForeignKey(
                to='tarmor.EQ_Type',
                on_delete=models.PROTECT,
            )
        ),
        # Convert Equipment.Asset_Type TEXT → FK
        migrations.AlterField(
            model_name='equipment',
            name='Asset_Type',
            field=models.ForeignKey(
                to='tarmor.AssetType',
                on_delete=models.PROTECT
            )
        ),
        migrations.RunPython(convert_data),
    ]