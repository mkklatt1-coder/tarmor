from django.db import models
from django.utils import timezone

class Garage(models.Model):
    name = models.CharField(max_length=100)
    # optional relationship to crew or users
    def __str__(self):
        return self.name
    
class WorkWeek(models.Model):
    week_number = models.PositiveSmallIntegerField(unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    
    def __str__(self):
        return f"Week {self.week_number} ({self.start_date} to {self.end_date})"
    
class Schedule(models.Model):
    week = models.ForeignKey(WorkWeek, on_delete=models.CASCADE)
    responsible_garage = models.ForeignKey(Garage, on_delete=models.PROTECT)
    locked = models.BooleanField(default=False)
    last_saved = models.DateTimeField(auto_now=True)
    locked_at = models.DateTimeField(null=True, blank=True)

    def lock(self):
        self.locked = True
        self.locked_at = timezone.now()
        self.save()

class WorkOrder(models.Model):
    work_order_no = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    planned_start = models.DateField(null=True, blank=True)
    estimated_hours = models.DecimalField(max_digits=6, decimal_places=2)
    responsible_garage = models.ForeignKey(Garage, on_delete=models.PROTECT)
    completion_date = models.DateField(null=True, blank=True)
    job_status = models.CharField(
        max_length=30,
        choices=[
            ("Waiting to Schedule", "Waiting to Schedule"),
            ("Reschedule", "Reschedule"),
            ("Execution", "Execution"),
        ],
        default="Waiting to Schedule",
    )
    def __str__(self):
        return f"{self.work_order_no}: {self.description[:40]}"
    
class ScheduleSnapshot(models.Model):
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)
    work_order = models.ForeignKey(WorkOrder, on_delete=models.PROTECT)
    planned_start_snapshot = models.DateField()
    estimated_hours_snapshot = models.DecimalField(max_digits=6, decimal_places=2)
    job_status_snapshot = models.CharField(max_length=30)
    completion_date_snapshot = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Snapshot of {self.work_order.work_order_no}"
