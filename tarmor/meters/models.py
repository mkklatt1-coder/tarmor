from django.db import models
from equipment.models import Equipment, Meter
from django.db.models import UniqueConstraint

REPLACED_CHOICES = [
        ('No', 'No'),
        ('Yes', 'Yes'),
    ]

class MeterReading(models.Model):
    Date = models.DateField(null=True, blank=True)
    Equipment = models.ForeignKey('equipment.Equipment', on_delete=models.CASCADE, related_name='readings')
    Meter_Replaced = models.CharField(max_length=10, choices=REPLACED_CHOICES, default='No')
    Meter_Type = models.ForeignKey('equipment.Meter', on_delete=models.CASCADE, related_name='history')
    Meter_Reading = models.IntegerField(null=True, blank=True)
    Reading_Difference = models.IntegerField(null=True, blank=True)
    Total_Meter_Value = models.IntegerField(null=True, blank=True)
    
    class Meta:
        db_table = 'tarmor_meterreading'
        constraints = [
            UniqueConstraint(
                fields=['Date', 'Equipment', 'Meter_Type'], 
                name='unique_daily_reading'
            )
        ]
        
def cascade_meter_update(meter_type_obj, start_date):
    """Recalculates all readings for a specific meter from a start date forward."""
    readings = MeterReading.objects.filter(
        Meter_Type=meter_type_obj, 
        Date__gt=start_date
    ).order_by('Date', 'id')

    for reading in readings:
        # Look for the log immediately BEFORE this one
        last_log = MeterReading.objects.filter(
            Meter_Type=reading.Meter_Type,
            Date__lt=reading.Date
        ).order_by('-Date', '-id').first()
        
        last_total = last_log.Total_Meter_Value if last_log else 0
        last_physical = last_log.Meter_Reading if last_log else 0

        if reading.Meter_Replaced == 'Yes':
            reading.Reading_Difference = 0
            reading.Total_Meter_Value = last_total
        else:
            # Re-calculate based on what the user originally entered
            # Priority 1: User entered a manual Reading_Difference
            # Priority 2: User entered a physical Meter_Reading
            if reading.Reading_Difference:
                reading.Total_Meter_Value = last_total + reading.Reading_Difference
                reading.Meter_Reading = last_physical + reading.Reading_Difference
            else:
                diff = reading.Meter_Reading - last_physical
                reading.Reading_Difference = diff
                reading.Total_Meter_Value = last_total + diff
        
        reading.save()