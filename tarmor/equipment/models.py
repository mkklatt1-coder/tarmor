from django.db import models

class AssetType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    class Meta:
        managed = True
        db_table = 'tarmor_assettype'
    def __str__(self):
        return self.name
    
class ComponentType(models.Model):
    name = models.CharField(max_length=100) # e.g., "Engine"
    short_code = models.CharField(max_length=5) # e.g., "ENG"
    asset_type = models.ForeignKey('AssetType', on_delete=models.CASCADE, related_name='component_types')

    def __str__(self):
        return f"{self.name} ({self.short_code})"

    class Meta:
        verbose_name_plural = "Component Types"
        ordering = ['name']
        unique_together = (('short_code', 'asset_type'), ('name', 'asset_type'))
        
class EQ_Type(models.Model):
    Asset_Type = models.ForeignKey('AssetType', on_delete=models.CASCADE, related_name="equipment_types", db_column='Asset_Type')
    Equipment_Type = models.CharField(max_length=50)
    Prefix = models.CharField(max_length=10)
    class Meta:
        managed = True
        db_table = 'tarmor_eq_type'
        unique_together = ('Asset_Type', 'Equipment_Type')
    def __str__(self):
        return self.Equipment_Type
    
CAB_CHOICES = [
    ('Open', 'Open'),
    ('Enclosed', 'Enclosed')
]

TIER_CHOICES = [
    ('N/A', 'N/A'),
    ('Tier 2', 'Tier 2'),
    ('Tier 3', 'Tier 3'),
    ('Tier 4', 'Tier 4'),
]

BOX_CHOICES = [
    ('Dump', 'Dump'),
    ('Ejector', 'Ejector')
]

class Equipment(models.Model):
    Equipment_Number = models.CharField(max_length=20, unique=True)
    Asset_Type = models.ForeignKey('AssetType', on_delete=models.PROTECT)
    Equipment_Type = models.ForeignKey(EQ_Type, on_delete=models.PROTECT, db_column='Equipment_Type')
    Equipment_Status = models.CharField(max_length=50)
    Equipment_Description = models.CharField(max_length=255, blank=True)
    Commissioning_Date = models.DateField(null=True, blank=True)
    Decommissioning_Date = models.DateField(null=True, blank=True)
    Make = models.CharField(max_length=50, blank=True)
    Model = models.CharField(max_length=50, blank=True)
    Serial_Number = models.CharField(max_length=50, blank=True)
    PO_Number = models.CharField(max_length=50, blank=True)
    Equipment_Value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    Warranty_Start_Date = models.DateField(null=True, blank=True)
    Warranty_End_Date = models.DateField(null=True, blank=True)
    Engine_HP_Rating = models.IntegerField(null=True, blank=True)
    CANMET_Number = models.CharField(max_length=50, blank=True)
    Ventilation_Rating = models.CharField(max_length=50, blank=True)
    Garage = models.ForeignKey('facilities.Facility', to_field='Facility_Name', on_delete=models.PROTECT, blank=True, null=True)
    Overhaul_Period = models.IntegerField(null=True, blank=True)
    Overhaul_Value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    End_of_Life = models.IntegerField(null=True, blank=True)
    Cab_Style = models.CharField(choices=CAB_CHOICES, null=True, blank=True)
    Eng_Tier = models.CharField(choices=TIER_CHOICES, null=True, blank=True)
    Box_Type = models.CharField(choices=BOX_CHOICES, null=True, blank=True)
    
    Additional_Information = models.TextField(blank=True)
    
    class Meta:
        managed = True
        db_table = 'tarmor_equipment'
    
    def __str__(self):
        return self.Equipment_Number
    
METER_CHOICES = [
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

class Meter(models.Model):
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='meters')
    meter_type = models.CharField(max_length=50, choices=METER_CHOICES)
    
    class Meta:
        db_table = 'tarmor_meter'
        
    def __str__(self):
        return f"{self.meter_type} ({self.equipment.Equipment_Number})"


class Component(models.Model):
    STATUS_CHOICES = [
        ('Installed', 'Installed'),
        ('Spare', 'Spare'),
        ('Retired', 'Retired'),
    ]
        
    Equipment = models.ForeignKey('Equipment', db_column='Equipment_Number', on_delete=models.CASCADE, related_name='components')
    Status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    Installation_Date = models.DateField(null=True, blank=True)
    Removal_Date = models.DateField(null=True, blank=True)
    Component_Number = models.CharField(max_length=50, unique=True)
    Component_Description = models.CharField(max_length=100)
    Component_Type = models.ForeignKey('ComponentType', on_delete=models.PROTECT)
    Make = models.CharField(max_length=50, blank=True)
    Model = models.CharField(max_length=50, blank=True)
    Serial_Number = models.CharField(max_length=50, blank=True)
    Expected_Lifespan = models.IntegerField(null=True, blank=True)
    UoM = models.CharField(max_length=10, choices=[('Hours', 'Hours'), ('Kms', 'Kms'), ('Cycles', 'Cycles'), ('Years', 'Years')], default='Hours')
    PO_Number = models.CharField(max_length=50, blank=True)
    Warranty_Duration = models.IntegerField(null=True, blank=True)
    Wty_UoM = models.CharField(max_length=10, choices=[('Hours', 'Hours'), ('Kms', 'Kms'), ('Cycles', 'Cycles'), ('Years', 'Years')], default='Hours')
    Warranty_Start_Date = models.DateField(null=True, blank=True)
    Warranty_End_Date = models.DateField(null=True, blank=True)
    Additional_Information = models.TextField(blank=True)
        
    class Meta:
        db_table = 'tarmor_component'
    
    def __str__(self):
        return f"{self.Component_Number} ({self.Component_Type})"
    
    
class ComponentHistory(models.Model):
    CHANGE_TYPE_CHOICES=[
        ('Replaced New', 'Replaced New'),
        ('Replaced Reman', 'Replaced Reman'),
        ('Rebuilt', 'Rebuilt'),
    ]
    
    METER_CHOICES = [
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
    
    Component = models.ForeignKey('Component', on_delete=models.CASCADE, related_name='history')
    Equipment = models.ForeignKey('Equipment', on_delete=models.CASCADE)
    
    # Event Data
    Work_Order_Number = models.CharField(max_length=50)
    Change_Date = models.DateField()
    Change_Type = models.CharField(max_length=50, choices=CHANGE_TYPE_CHOICES)
    
    # Meter Snapshot
    Meter_Description = models.CharField(max_length=50, choices=METER_CHOICES)
    Meter_Reading = models.DecimalField(max_digits=12, decimal_places=0)
    
    # The "Swap" Details
    Old_Serial = models.CharField(max_length=50)
    New_Serial = models.CharField(max_length=50)
    New_Make = models.CharField(max_length=50)
    New_Model = models.CharField(max_length=50)
    New_PO = models.CharField(max_length=50)
    New_Lifespan = models.CharField(max_length=50)
    New_UoM = models.CharField(max_length=10)
    New_Wty_Dur = models.CharField(max_length=50)
    New_Wty_UoM = models.CharField(max_length=10)
    New_Wty_Start = models.DateField(null=True, blank=True)
    New_Wty_End = models.DateField(null=True, blank=True)
    
    # Extra Info
    Additional_Information = models.TextField(blank=True)
    Date_Recorded = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tarmor_component_history'
        ordering = ['-Change_Date']

    def __str__(self):
        return f"Swap: {self.Component.Component_Number} on {self.Change_Date}"
    
class ShiftReport(models.Model):
    asset_type = models.ForeignKey(AssetType, on_delete=models.SET_NULL, null=True, blank=True)
    garage = models.ForeignKey('facilities.Facility', on_delete=models.SET_NULL, null=True, blank=True, related_name='shift_reports')
    date = models.DateField()
    shift = models.CharField(max_length=2, choices=[('DS', 'Day Shift'), ('NS', 'Night Shift')])
    mining_supervisor = models.CharField(max_length=100)
    maint_supervisor = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    hourly_data = models.JSONField(default=dict)

    class Meta:
        unique_together = ('date', 'shift') # Prevents duplicate reports for the same shift

class MachineShiftStatus(models.Model):
    report = models.ForeignKey(ShiftReport, on_delete=models.CASCADE, related_name='statuses')
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE)
    total_down = models.FloatField(default=0.0)
    total_worked = models.FloatField(default=0.0)
    available = models.FloatField(default=12.0)
    final_status = models.CharField(max_length=10, choices=[('Available', 'Available'), ('Down', 'Down')])
    # Storing the 44 quadrants as a string or JSON to reload the grid later
    grid_data = models.TextField(help_text="Comma-separated D, W, P, or empty values")