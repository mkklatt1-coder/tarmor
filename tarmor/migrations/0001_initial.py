from django.db import migrations, models

class Migration(migrations.Migration):
    initial = True
    dependencies = [
    ]
    operations = [
        migrations.CreateModel(
            name='AssetType',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='EQ_Type',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('Equipment_Type', models.CharField(max_length=50)),
                ('Prefix', models.CharField(max_length=10)),
                ('Asset_Type', models.CharField(max_length=50)),   # TEMPORARY (converted later in migration 0002)
            ],
        ),
        migrations.CreateModel(
            name='Equipment',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('Equipment_Number', models.CharField(max_length=20, unique=True)),
                ('Equipment_Status', models.CharField(max_length=50)),
                ('Equipment_Description', models.CharField(max_length=255, blank=True)),
                ('Commissioning_Date', models.DateField(null=True, blank=True)),
                ('Decommissioning_Date', models.DateField(null=True, blank=True)),
                ('Make', models.CharField(max_length=50, blank=True)),
                ('Model', models.CharField(max_length=50, blank=True)),
                ('Serial_Number', models.CharField(max_length=50, blank=True)),
                ('PO_Number', models.CharField(max_length=50, blank=True)),
                ('Equipment_Value', models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)),
                ('Warranty_Start_Date', models.DateField(null=True, blank=True)),
                ('Warranty_End_Date', models.DateField(null=True, blank=True)),
                ('Engine_HP_Rating', models.IntegerField(null=True, blank=True)),
                ('CANMET_Number', models.CharField(max_length=50, blank=True)),
                ('Ventilation_Rating', models.CharField(max_length=50, blank=True)),
                ('Responsible_Garage', models.CharField(max_length=50, blank=True)),
                ('Additional_Information', models.TextField(blank=True)),
                ('Asset_Type', models.CharField(max_length=50)),     # TEMPORARY (converted later)
                ('Equipment_Type', models.CharField(max_length=50)), # TEMPORARY (converted later)
            ],
        ),
        migrations.CreateModel(
            name='Meter',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('meter_type', models.CharField(
                    max_length=50,
                    choices=[
                        ('','Select'),
                        ('Engine Hours', 'Engine Hours'),
                        ('Odometer', 'Odometer'),
                        ('Power Pack Hours', 'Power Pack Hours'),
                        ('Power Pack Left', 'Power Pack Left'),
                        ('Power Pack Right', 'Power Pack Right'),
                        ('Impact Hours', 'Impact Hours'),
                        ('Impact Left', 'Impact Left'),
                        ('Impact Right', 'Impact Right'),
                        ('Operating Hours', 'Operating Hours'),
                    ]
                )),
                ('equipment', models.ForeignKey(
                    on_delete=models.CASCADE,
                    related_name='meters',
                    to='tarmor.Equipment'
                )),
            ],
        ),
    ]