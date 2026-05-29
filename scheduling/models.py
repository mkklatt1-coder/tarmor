from django.db import models
from django.utils import timezone
from datetime import timedelta
from facilities.models import Facility
from equipment.models import Equipment
from work_orders.models import WorkOrder
from personnel.models import Employee, Crew

DAYS_OF_WEEK = [
    ("Monday", "Monday"),
    ("Tuesday", "Tuesday"),
    ("Wednesday", "Wednesday"),
    ("Thursday", "Thursday"),
    ("Friday", "Friday"),
    ("Saturday", "Saturday"),
    ("Sunday", "Sunday"),
]
class WeekSetup(models.Model):
    start_day = models.CharField(max_length=10, choices=DAYS_OF_WEEK, default="Monday")
    week1_start_date = models.DateField(verbose_name="Start Date for Week 1")
    active = models.BooleanField(default=True, help_text="Only one active setup should exist at a time")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.start_day} start — Week 1: {self.week1_start_date}"
    
    def save(self, *args, **kwargs):
        """Deactivate other rows and rebuild WorkWeek entries."""
        if self.active:
            WeekSetup.objects.exclude(pk=self.pk).update(active=False)
        super().save(*args, **kwargs)
        WorkWeek.generate_weeks(self)
    
class WorkWeek(models.Model):
    setup = models.ForeignKey(WeekSetup, on_delete=models.CASCADE, related_name="weeks")
    week_number = models.PositiveSmallIntegerField()
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        unique_together = ("setup", "week_number")
        ordering = ["week_number"]

    def __str__(self):
        return f"Week {self.week_number} ({self.start_date}–{self.end_date})"
    
    @staticmethod
    def generate_weeks(setup, total_weeks=52):
        from datetime import timedelta
        # Remove old weeks for this setup
        WorkWeek.objects.filter(setup=setup).delete()
        base_date = setup.week1_start_date
        for i in range(total_weeks):
            start = base_date + timedelta(days=i * 7)
            end = start + timedelta(days=6)
            WorkWeek.objects.create(
                setup=setup,
                week_number=i + 1,
                start_date=start,
                end_date=end,
            )
    
class Schedule(models.Model):
    week = models.ForeignKey(WorkWeek, on_delete=models.CASCADE)
    responsible_garage = models.ForeignKey(Facility, verbose_name="Garage", on_delete=models.PROTECT)
    locked = models.BooleanField(default=False)
    locked_at = models.DateTimeField(null=True, blank=True)
    last_saved = models.DateTimeField(auto_now=True)

    def lock(self):
        self.locked = True
        self.locked_at = timezone.now()
        self.save()

class ScheduleSnapshot(models.Model):
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name="snapshots")
    work_order = models.ForeignKey(WorkOrder, on_delete=models.PROTECT)
    plan_start_snapshot = models.DateField()
    estimated_hours_snapshot = models.DecimalField(max_digits=6, decimal_places=2)
    job_status_snapshot = models.CharField(max_length=50)
    date_closed_snapshot = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Snapshot {self.work_order.work_order}"
    
class DailyCrewCapacity(models.Model):
    crew = models.ForeignKey(Crew, on_delete=models.PROTECT)
    workweek = models.ForeignKey(WorkWeek, on_delete=models.CASCADE)
    date = models.DateField()
    available_hours = models.DecimalField(max_digits=5, decimal_places=2)
    assigned_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)

class TimeOffLog(models.Model):
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='time_off_logs')
    date = models.DateField()
    ds_off = models.IntegerField(default=0)
    ns_off = models.IntegerField(default=0)

    class Meta:
        db_table = 'tarmor_time_off_log'
        unique_together = ('facility', 'date')

    def __str__(self):
        return f"Time Off {self.date} - DS: {self.ds_off}h, NS: {self.ns_off}h"
