from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

time_choices = [
    ('Prep', 'Prep'),
    ('Travel', 'Travel'),
    ('Troubleshoot', 'Troubleshoot'),
    ('Repair','Repair')
]

class Timesheet(models.Model):
    work_order = models.ForeignKey(
        'work_orders.WorkOrder',
        on_delete=models.PROTECT,
        db_column='work_order',
    )
    technician = models.ForeignKey(
        'personnel.Employee',
        on_delete=models.PROTECT,
        related_name='timesheets'
    )
    start_date = models.DateTimeField(default=timezone.now)
    finish_date = models.DateTimeField(default=timezone.now)
    total_time = models.FloatField(null=True, blank=True)
    time_type = models.CharField(max_length=15, choices=time_choices,)
    
    def clean(self):
        if self.start_date and self.finish_date and self.finish_date < self.start_date:
            raise ValidationError("Finish date cannot be earlier than start date.")
    
    def save(self, *args, **kwargs):
        self.full_clean()
        if self.start_date and self.finish_date:
            diff = self.finish_date - self.start_date
            self.total_time = round(diff.total_seconds() / 3600, 2)
        super().save(*args, **kwargs)