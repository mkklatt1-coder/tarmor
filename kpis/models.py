from django.db import models

class FailureFrequency(models.Model):
    equipment_number = models.CharField(max_length=50)
    equipment_description = models.CharField(max_length=255)
    asset_type = models.CharField(max_length=100)
    equipment_type = models.CharField(max_length=100)
    equipment_hours = models.FloatField(help_text="Accumulated hours in range")
    failure_count = models.IntegerField()
    frequency = models.FloatField(help_text="Failures per hour")
    start_date = models.DateField()
    end_date = models.DateField()

    def save(self, *args, **kwargs):
        # Auto-calculate frequency before saving
        if self.equipment_hours > 0:
            self.frequency = self.failure_count / self.equipment_hours
        else:
            self.frequency = 0
        super().save(*args, **kwargs)

class MTBF(models.Model):
    equipment_number = models.CharField(max_length=50)
    equipment_description = models.CharField(max_length=255)
    asset_type = models.CharField(max_length=100)
    equipment_type = models.CharField(max_length=100)
    equipment_hours = models.FloatField(help_text="Accumulated hours in range")
    failure_count = models.IntegerField()
    mtbf = models.FloatField(help_text="Mean Time Between Failures")
    start_date = models.DateField()
    end_date = models.DateField()

    def save(self, *args, **kwargs):
        # Auto-calculate MTBF before saving
        if self.equipment_hours > 0:
            self.mtbf = self.equipment_hours / self.failure_count
        else:
            self.mtbf = 0
        super().save(*args, **kwargs)