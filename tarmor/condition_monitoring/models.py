from django.db import models
from equipment.models import Equipment, Meter, AssetType, EQ_Type
from work_orders.models import WorkOrder
from purchasing.models import Purchase
from dateutil.relativedelta import relativedelta

progress_choices = [
    ('Pending', 'Pending'),
    ('In Progress', 'In Progress'),
    ('Complete', 'Complete'),
    ('Canceled', 'Canceled'),
]

yesno_choices = [
    ('Yes', 'Yes'),
    ('No', 'No'),
]

compartment_choices = [
    ('Engine', 'Engine'),
    ('Transmission', 'Transmission'),
    ('Trans Mag Strain', 'Trans Mag Strain'),
    ('Upbox', 'Upbox'),
    ('Dropbox', 'Dropbox'),
    ('Hydraulic', 'Hydraulic'),
    ('Front Diff', 'Front Diff'),
    ('Centre Diff', 'Centre Diff'),
    ('Rear Diff', 'Rear Diff'),
]

plug_choices = [
    (1, '1 - Excellent'),
    (2, '2 - Good'),
    (3, '3 - Fair'),
    (4, '4 - Poor'),
    (5, '5 - Critical Failure'),
]

filter_choices = [
    (1, '1 - Good'),
    (2, '2 - Fair'),
    (3, '3 - Poor'),
    (4, '4 - Critical Failure'),
]

class ShortTermCM(models.Model):
    date = models.DateField()
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, null=True, blank=True, related_name='shortterm_equipment')
    equipment_desc = models.CharField(max_length=255, null=True, blank=True)
    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, null=True, blank=True, related_name='shortterm_wo')
    troubleshoot_desc = models.TextField(null=True, blank=True)
    repair_desc = models.TextField(null=True, blank=True)
    problem = models.CharField(max_length=255)
    corrective_action = models.CharField(max_length=255)
    due_date = models.DateField()
    progress = models.CharField(max_length=15, choices=progress_choices)
    completed_date = models.DateField(null=True, blank=True)
    complete = models.CharField(max_length=15, choices=yesno_choices)

class MagPlug(models.Model):
    date = models.DateField()
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, null=True, blank=True, related_name='mag_plug_eq')
    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, null=True, blank=True, related_name='mag_plug_wo')
    meter_reading = models.IntegerField(null=True, blank=True)
    meter = models.ForeignKey(Meter, on_delete=models.CASCADE, null=True, blank=True, related_name='mag_plug_mtr')
    compartment = models.CharField(choices=compartment_choices, null=True, blank=True)
    plug_rating = models.IntegerField(choices=plug_choices, null=True, blank=True)
    comments = models.CharField(max_length=255, null=True, blank=True)

class FilterRating(models.Model):
    date = models.DateField()
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, null=True, blank=True, related_name='filter_rating_eq')
    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, null=True, blank=True, related_name='filter_rating_wo')
    meter_reading = models.IntegerField(null=True, blank=True)
    meter = models.ForeignKey(Meter, on_delete=models.CASCADE, null=True, blank=True, related_name='filter_rating_mtr')
    compartment = models.CharField(choices=compartment_choices, null=True, blank=True)
    filter_rating = models.IntegerField(choices=filter_choices, null=True, blank=True)
    comments = models.CharField(max_length=255, null=True, blank=True)

class ValveSet(models.Model):
    date = models.DateField()
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, null=True, blank=True, related_name='valve_sets')
    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, null=True, blank=True, related_name='valve_sets')
    meter = models.ForeignKey(Meter, on_delete=models.CASCADE, null=True, blank=True, related_name='valve_sets')
    meter_reading = models.IntegerField(null=True, blank=True)
    comments = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        ordering = ['-date', '-id']
    def __str__(self):
        return f'{self.date} - {self.equipment} - WO {self.work_order}'
    
class ValveSetReading(models.Model):
    CYLINDER_CHOICES = [
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5'),
        ('6', '6'),
        ('7', '7'),
        ('8', '8'),
    ]
    INT_EXH_CHOICES = [
        ('Int', 'Intake'),
        ('Exh', 'Exhaust'),
    ]
    VALVE_CHOICES = [
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
    ]

    valve_set = models.ForeignKey(ValveSet, on_delete=models.CASCADE, related_name='readings')
    cylinder_number = models.CharField(max_length=2, choices=CYLINDER_CHOICES, null=True, blank=True)
    int_exh = models.CharField(max_length=3, choices=INT_EXH_CHOICES, null=True, blank=True)
    valve_number = models.CharField(max_length=2, choices=VALVE_CHOICES, null=True, blank=True)
    valve_setting = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)

    class Meta:
        ordering = ['cylinder_number', 'int_exh', 'valve_number']
    def __str__(self):
        return f'Cyl {self.cylinder_number} {self.int_exh} Valve {self.valve_number}: {self.valve_setting}'
    
class CylinderTemp(models.Model):
    date = models.DateField()
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, null=True, blank=True, related_name='cylinder_temps')
    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, null=True, blank=True, related_name='cylinder_temps')
    meter = models.ForeignKey(Meter, on_delete=models.CASCADE, null=True, blank=True, related_name='cylinder_temps')
    meter_reading = models.IntegerField(null=True, blank=True)
    comments = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        ordering = ['-date', '-id']
    def __str__(self):
        return f'{self.date} - {self.equipment} - WO {self.work_order}'
    
class CylinderTempReading(models.Model):
    CYLINDER_CHOICES = [
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5'),
        ('6', '6'),
        ('7', '7'),
        ('8', '8'),
        ('Turbo', 'Turbo'),
    ]

    DEGREES_CHOICES = [
        ('degrees C', 'degrees C'),
        ('degrees F', 'degrees F'),
    ]
    
    cylinder_temp = models.ForeignKey(CylinderTemp, on_delete=models.CASCADE, related_name='cyl_temp_readings')
    cylinder_number = models.CharField(max_length=6, choices=CYLINDER_CHOICES, null=True, blank=True)
    temp_reading = models.CharField(max_length=4, null=True, blank=True)
    uom = models.CharField(max_length=10, choices=DEGREES_CHOICES, null=True, blank=True)

    class Meta:
        ordering = ['cylinder_number', 'temp_reading', 'uom']
    def __str__(self):
        return f'Cyl {self.cylinder_number} {self.temp_reading} {self.uom}'
    
class BucketLip(models.Model):
    date = models.DateField()
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, null=True, blank=True, related_name='bucket_lips')
    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, null=True, blank=True, related_name='bucket_lips')
    meter = models.ForeignKey(Meter, on_delete=models.CASCADE, null=True, blank=True, related_name='bucket_lips')
    meter_reading = models.IntegerField(null=True, blank=True)
    comments = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        ordering = ['-date', '-id']
    def __str__(self):
        return f'{self.date} - {self.equipment} - WO {self.work_order}'
    
class LipMeasurement(models.Model):
    bucket_lip = models.ForeignKey(BucketLip, on_delete=models.CASCADE, related_name='lip_measurements')
    left_side = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    right_side = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    centre = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ['left_side', 'right_side', 'centre']
    def __str__(self):
        return f'Left: {self.left_side}, Right: {self.right_side}, Centre: {self.centre}'
    
class BoxLiner(models.Model):
    date = models.DateField()
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, null=True, blank=True, related_name='box_liners')
    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, null=True, blank=True, related_name='box_liners')
    meter = models.ForeignKey(Meter, on_delete=models.CASCADE, null=True, blank=True, related_name='box_liners')
    meter_reading = models.IntegerField(null=True, blank=True)
    comments = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        ordering = ['-date', '-id']
    def __str__(self):
        return f'{self.date} - {self.equipment} - WO {self.work_order}'
    
class LinerMeasurement(models.Model):
    POSITION_CHOICES = [
        ('Pos 1', 'Pos 1'),
        ('Pos 2', 'Pos 2'),
        ('Pos 3', 'Pos 3'),
        ('Pos 4', 'Pos 4'),
        ('Pos 5', 'Pos 5'),
        ('Pos 6', 'Pos 6'),
        ('Pos 7', 'Pos 7'),
        ('Pos 8', 'Pos 8'),
        ('Pos 9', 'Pos 9'),
        ('Pos 10', 'Pos 10'),
        ('Pos 11', 'Pos 11'),
        ('Pos 12', 'Pos 12'),
        ('Pos 13', 'Pos 13'),
    ]

    box_liner = models.ForeignKey(BoxLiner, on_delete=models.CASCADE, related_name='liner_measurements')
    position = models.CharField(max_length=6, choices=POSITION_CHOICES, null=True, blank=True)
    pos_reading = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ['position', 'pos_reading']
    def __str__(self):
        return f'Position {self.position}: {self.pos_reading}'
    
class CycleTime(models.Model):
    date = models.DateField()
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, null=True, blank=True, related_name='cycle_times')
    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, null=True, blank=True, related_name='cycle_times')
    meter = models.ForeignKey(Meter, on_delete=models.CASCADE, null=True, blank=True, related_name='cycle_times')
    meter_reading = models.IntegerField(null=True, blank=True)
    comments = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        ordering = ['-date', '-id']
    def __str__(self):
        return f'{self.date} - {self.equipment} - WO {self.work_order}'
    
class CycleTimeMeasurement(models.Model):
    SYSTEM_CHOICES = [
        ('Steering', 'Steering'),
        ('Ejector', 'Ejector'),
        ('Lift', 'Lift'),
        ('Tilt', 'Tilt'),
        ('Boom', 'Boom'),
        ('Stick', 'Stick'),
        ('Turret', 'Turret'),
        ('Telescopic', 'Telescopic'),
        ('House', 'House'),
        ('Scissor', 'Scissor'),
        ('Drill Feed', 'Drill Feed'),
        ('Bolt Feed', 'Bolt Feed'),
        ('Boom Feed', 'Boom Feed'),
    ]

    SYS_POS_CHOICES = [
        ('Left', 'Left'),
        ('Right', 'Right'),
        ('Up', 'Up'),
        ('Down', 'Down'),
        ('Tilt', 'Tilt'),
        ('Rollback', 'Rollback'),
        ('Extend', 'Extend'),
        ('Retract', 'Retract'),
        ('Swing/Rotate CW', 'Swing/Rotate CW'),
        ('Swing/Rotate CCW', 'Swing/Rotate CCW'),
        ('In', 'Int'),
        ('Out', 'Out'),
    ]

    cycle_time = models.ForeignKey(CycleTime, on_delete=models.CASCADE, related_name='cycle_time_measurements')
    system = models.CharField(max_length=50, choices=SYSTEM_CHOICES, null=True, blank=True)
    position = models.CharField(max_length=50, choices=SYS_POS_CHOICES, null=True, blank=True)
    time = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ['system', 'time']
    def __str__(self):
        return f'System {self.system}: {self.time}'

class TireInformation(models.Model):
    FACE_CHOICES = [
        ('Smooth', 'Smooth'),
        ('Treaded', 'Treaded'),
    ]

    asset_type = models.ForeignKey(AssetType, on_delete=models.CASCADE, null=True, blank=True, related_name='tire_info_asset')
    equipment_type = models.ForeignKey(EQ_Type, on_delete=models.CASCADE, null=True, blank=True, related_name='tire_info_eq')
    make = models.CharField(max_length=50, null=True, blank=True)
    model = models.CharField(max_length=50, null=True, blank=True)
    tire_size = models.CharField(max_length=50, null=True, blank=True)
    tire_face = models.CharField(max_length=50, choices=FACE_CHOICES, null=True, blank=True)
    tread_depth_new = models.IntegerField(null=True, blank=True)
    inflation_pressure = models.IntegerField(null=True, blank=True)
    tire_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

class TireChange(models.Model):
    date = models.DateField()
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, null=True, blank=True, related_name='tire_changes')
    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, null=True, blank=True, related_name='tire_changes')
    meter = models.ForeignKey(Meter, on_delete=models.CASCADE, null=True, blank=True, related_name='tire_changes')
    meter_reading = models.IntegerField(null=True, blank=True)
    comments = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        ordering = ['-date', '-id']
    def __str__(self):
        return f'{self.date} - {self.equipment} - WO {self.work_order}'
    
wheel_position_choices = [
        ('Front Left', 'Front Left'),
        ('Front Right', 'Front Right'),
        ('Centre Left', 'Centre Left'),
        ('Centre Right', 'Centre Right'),
        ('Centre Outside Left', 'Centre Outside Left'),
        ('Centre Outside Right', 'Centre Outside Right'),
        ('Centre Inside Left', 'Centre Inside Left'),
        ('Centre Inside Right', 'Centre Inside Right'),
        ('Rear Left', 'Rear Left'),
        ('Rear Right', 'Rear Right'),
        ('Rear Outside Left', 'Rear Outside Left'),
        ('Rear Outside Right', 'Rear Outside Right'),
        ('Rear Inside Left', 'Rear Inside Left'),
        ('Rear Inside Right', 'Rear Inside Right'),        
    ]

class TireChangeInfo(models.Model):
    
    tire_change = models.ForeignKey(TireChange, on_delete=models.CASCADE, related_name='tire_change_info')
    tire_id_off = models.CharField(max_length=50, null=True, blank=True)
    tire_id_on = models.CharField(max_length=50, null=True, blank=True)
    position = models.CharField(max_length=50, choices=wheel_position_choices, null=True, blank=True)
    tread_depth_off = models.IntegerField(null=True, blank=True)
    tread_depth_on = models.IntegerField(null=True, blank=True)
    rim_id_off = models.CharField(max_length=50, null=True, blank=True)
    rim_id_on = models.CharField(max_length=50, null=True, blank=True)
    purchase_order = models.ForeignKey(Purchase, on_delete=models.SET_NULL, null=True, blank=True, related_name='tire_changes')
    tire_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    reason_for_failure = models.ForeignKey('TireFailure', on_delete=models.SET_NULL, null=True, blank=True, related_name='tire_changes_failure')
    inflation_pressure = models.IntegerField(null=True, blank=True)
    scrapped = models.CharField(max_length=3, choices=yesno_choices, null=True, blank=True)
    recapped = models.CharField(max_length=3, choices=yesno_choices, null=True, blank=True)
    scrap_reason = models.ForeignKey('TireFailure', on_delete=models.SET_NULL, null=True, blank=True, related_name='tire_changes_scrap')

class TireFailure(models.Model):
    failure_mode = models.CharField(max_length=50, null=True, blank=True)
    def __str__(self):
        return self.failure_mode if self.failure_mode else "Unnamed Failure Mode"
    

class TireInspection(models.Model):
    date = models.DateField()
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, null=True, blank=True, related_name='tire_inspections')
    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, null=True, blank=True, related_name='tire_inspections')
    meter = models.ForeignKey(Meter, on_delete=models.CASCADE, null=True, blank=True, related_name='tire_inspections')
    meter_reading = models.IntegerField(null=True, blank=True)
    comments = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        ordering = ['-date', '-id']
    def __str__(self):
        return f'{self.date} - {self.equipment} - WO {self.work_order}'
    
class TireInspectionReading(models.Model):
    tire_inspection = models.ForeignKey(TireInspection, on_delete=models.CASCADE, related_name='tire_inspection_readings')
    tire_id = models.CharField(max_length=50, null=True, blank=True)
    position = models.CharField(max_length=50, choices=wheel_position_choices, null=True, blank=True)
    tread_depth = models.IntegerField(null=True, blank=True)
    inflation_pressure = models.IntegerField(null=True, blank=True)
    tire_diameter = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f'Position {self.position}: Tread Depth {self.tread_depth}, Inflation {self.inflation_pressure}, Diameter {self.tire_diameter}'
    
class RimInspection(models.Model):
    pass_fail_choices = [
        ('New', 'New'),
        ('Pass', 'Pass'),
        ('Fail', 'Fail'),
    ]
    
    failure_reason_choices = [
        ('Bent', 'Bent'),
        ('Cracked', 'Cracked'),
        ('Corroded', 'Corroded'),
        ('Excessive Wear', 'Excessive Wear'),
        ('Centre Plate Damage', 'Centre Plate Damage'),
        ('Run Flat', 'Run Flat'),
        ('Lock Ring Groove Failure', 'Lock Ring Groove Failure'),
        ('Gutter Section Failure', 'Gutter Section Failure'),
        ('Other', 'Other'),
    ]

    date_tested = models.DateField()
    rim_id = models.CharField(max_length=255, null=True, blank=True)
    pass_fail = models.CharField(max_length=4, choices=pass_fail_choices, null=True, blank=True)
    failure_reason = models.CharField(max_length=50, choices=failure_reason_choices, null=True, blank=True)
    last_test_date = models.DateField(null=True, blank=True)
    number_of_tests = models.IntegerField(null=True, blank=True)
    next_test_date = models.CharField(max_length=20, null=True, blank=True)

    class Meta:
        ordering = ['-date_tested', '-id']
        
    def __str__(self):
        return f'{self.date_tested} - {self.rim_id} - {self.pass_fail} - {self.failure_reason} - {self.next_test_date}'

    def save(self, *args, **kwargs):
        if self.pass_fail == 'Fail':
            self.next_test_date = "scrap"
            
        elif self.pass_fail == 'Pass' and self.date_tested:
            calculated_future_date = self.date_tested + relativedelta(years=2)
            self.next_test_date = calculated_future_date.strftime('%Y-%m-%d')
            
        else:
            self.next_test_date = None
        super().save(*args, **kwargs)
    