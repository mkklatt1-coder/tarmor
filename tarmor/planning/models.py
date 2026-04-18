from datetime import timedelta
from decimal import Decimal
import math
from dateutil.relativedelta import relativedelta
from django.db import models, transaction
from django.db.models import Sum
from django.utils import timezone
    
class QualityMaintenance(models.Model):
    QM_TYPE_CHOICES = [
        ('CALENDAR', 'Calendar'),
        ('METER', 'Meter'),
    ]
    STEP_TYPE_CHOICES = [
        ('SINGLE', 'Single Step'),
        ('MULTI', 'Multi-Step'),
    ]
    CALENDAR_UNIT_CHOICES = [
        ('DAY', 'Days'),
        ('WEEK', 'Weeks'),
        ('MONTH', 'Months'),
        ('YEAR', 'Years'),
    ]
    qm_number = models.CharField(max_length=9, unique=True)
    equipment = models.ForeignKey(
        'equipment.Equipment',
        on_delete=models.CASCADE,
        related_name='quality_maintenances'
    )
    description = models.CharField(max_length=255, blank=True)
    qm_type = models.CharField(max_length=10, choices=QM_TYPE_CHOICES)
    work_order_lead_days = models.PositiveIntegerField(default=14)
    step_type = models.CharField(max_length=10, choices=STEP_TYPE_CHOICES)
    start_date = models.DateField()
    # meter-specific
    meter_start = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    meter_type = models.ForeignKey(
        'equipment.Meter',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='quality_maintenances'
    )
    # single-step interval
    single_interval_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    calendar_unit = models.CharField(max_length=10, choices=CALENDAR_UNIT_CHOICES, null=True, blank=True)
    est_work_hours = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True)
    single_interval_checklist = models.FileField(upload_to='qm_checklists/', null=True, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'planning_qualitymaintenance'
        ordering = ['qm_number']
    def __str__(self):
        return f'{self.qm_number} - {self.equipment}'
    def get_interval_unit_display_text(self):
        if self.qm_type == 'CALENDAR':
            return self.get_calendar_unit_display() if self.calendar_unit else ''
        if self.qm_type == 'METER':
            return str(self.meter_type) if self.meter_type else ''
        return ''
    def get_steps(self):
        return list(self.steps.order_by('step_order'))
    def get_last_completed_instance(self):
        return self.instances.filter(status='COMPLETE').order_by('-completed_date', '-id').first()
    def get_completed_count(self):
        return self.instances.filter(status='COMPLETE').count()
    def get_current_meter(self):
        if self.qm_type != 'METER' or not self.meter_type:
            return self.meter_start or Decimal('0')
        latest = self.equipment.readings.filter(
            Meter_Type=self.meter_type,
            Date__isnull=False,
            Total_Meter_Value__isnull=False,
        ).order_by('-Date', '-id').first()
        if latest and latest.Total_Meter_Value is not None:
            return Decimal(latest.Total_Meter_Value)
        return self.meter_start or Decimal('0')
    def get_average_daily_usage(self):
        if self.qm_type != 'METER' or not self.meter_type:
            return None
        readings = self.equipment.readings.filter(
            Meter_Type=self.meter_type,
            Date__isnull=False,
            Total_Meter_Value__isnull=False
        ).order_by('Date', 'id')
        readings = list(readings)
        if len(readings) < 2:
            return None
        total_usage = Decimal('0')
        total_days = Decimal('0')
        previous = None
        for reading in readings:
            if previous:
                days = (reading.Date - previous.Date).days
                usage = reading.Total_Meter_Value - previous.Total_Meter_Value
                if days > 0 and usage >= 0:
                    total_usage += Decimal(usage)
                    total_days += Decimal(days)
            previous = reading
        if total_days == 0:
            return None
        return total_usage / total_days
    def add_calendar_interval(self, base_date, interval_value, interval_unit):
        value = int(interval_value)
        if interval_unit == 'DAY':
            return base_date + timedelta(days=value)
        if interval_unit == 'WEEK':
            return base_date + timedelta(weeks=value)
        if interval_unit == 'MONTH':
            return base_date + relativedelta(months=value)
        if interval_unit == 'YEAR':
            return base_date + relativedelta(years=value)
        return base_date
    def _calendar_step_unit_group(self, unit):
        if unit in ['DAY', 'WEEK']:
            return 'DAY_BASED'
        if unit in ['MONTH', 'YEAR']:
            return 'MONTH_BASED'
        return None
    def _calendar_step_to_base_value(self, interval_value, interval_unit):
        """
        Convert intervals into a comparable base value.
        DAY_BASED:
        - DAY = days
        - WEEK = 7 * days
        MONTH_BASED:
        - MONTH = months
        - YEAR = 12 * months
        """
        value = int(interval_value)
        if interval_unit == 'DAY':
            return value
        if interval_unit == 'WEEK':
            return value * 7
        if interval_unit == 'MONTH':
            return value
        if interval_unit == 'YEAR':
            return value * 12
        return None
    def _add_calendar_base_interval(self, base_date, amount, group):
        if group == 'DAY_BASED':
            return base_date + timedelta(days=amount)
        if group == 'MONTH_BASED':
            return base_date + relativedelta(months=amount)
        return base_date
    def _elapsed_calendar_base_units(self, start_date, candidate_date, group):
        if group == 'DAY_BASED':
            return (candidate_date - start_date).days
        if group == 'MONTH_BASED':
            months = (candidate_date.year - start_date.year) * 12 + (candidate_date.month - start_date.month)
            if candidate_date.day < start_date.day:
                months -= 1
            return months
        return 0
    def get_multi_step_due_calendar(self):
        """
        Calendar multi-step logic:
        - user defines service intervals only, e.g. 1 month, 6 month, 12 month
        - next due is the next future threshold from start_date
        - if multiple intervals match, the largest interval wins
        """
        steps = self.get_steps()
        if not steps:
            return None, None
        start_date = self.start_date
        today = timezone.localdate()
        normalized_steps = []
        interval_to_step = {}
        groups = set()
        for step in steps:
            if not step.interval_unit or step.interval_value is None:
                continue
            group = self._calendar_step_unit_group(step.interval_unit)
            base_value = self._calendar_step_to_base_value(step.interval_value, step.interval_unit)
            if group and base_value and base_value > 0:
                normalized_steps.append(base_value)
                interval_to_step[base_value] = step
                groups.add(group)
        if not normalized_steps:
            return None, None
        if len(groups) > 1:
            return None, None
        group = groups.pop()
        smallest_interval = min(normalized_steps)
        candidate_date = start_date
        elapsed = self._elapsed_calendar_base_units(start_date, candidate_date, group)
        while candidate_date <= today:
            elapsed += smallest_interval
            candidate_date = self._add_calendar_base_interval(start_date, elapsed, group)
        for _ in range(10000):
            matching_intervals = [i for i in normalized_steps if elapsed % i == 0]
            if matching_intervals:
                winning_interval = max(matching_intervals)
                return candidate_date, interval_to_step[winning_interval]
            elapsed += smallest_interval
            candidate_date = self._add_calendar_base_interval(start_date, elapsed, group)
        return None, None
    def get_multi_step_due_meter(self, current_meter=None):
        """
        Meter multi-step logic:
        - user defines service intervals only, e.g. 250, 500, 1000, 2000
        - next due is the next future threshold above current_meter
        - if multiple intervals match, the largest interval wins
        """
        steps = self.get_steps()
        if not steps:
            return None, None
        if current_meter is None:
            current_meter = self.get_current_meter()
        current_meter = int(current_meter)
        interval_to_step = {}
        intervals = []
        for step in steps:
            try:
                interval = int(step.interval_value)
            except (TypeError, ValueError):
                continue
            if interval > 0:
                intervals.append(interval)
                interval_to_step[interval] = step
        if not intervals:
            return None, None
        smallest_interval = min(intervals)
        candidate = current_meter + 1
        remainder = candidate % smallest_interval
        if remainder != 0:
            candidate += (smallest_interval - remainder)
        for _ in range(100000):
            matching_intervals = [interval for interval in intervals if candidate % interval == 0]
            if matching_intervals:
                winning_interval = max(matching_intervals)
                return Decimal(candidate), interval_to_step[winning_interval]
            candidate += smallest_interval
        return None, None
    def get_next_due(self, current_meter=None):
        today = timezone.localdate()
        if self.qm_type == 'CALENDAR':
            if self.step_type == 'SINGLE':
                if not self.single_interval_value or not self.calendar_unit:
                    return {
                        'next_due_date': None,
                        'next_due_meter': None,
                        'step': None,
                    }
                next_due_date = self.add_calendar_interval(
                    self.start_date,
                    self.single_interval_value,
                    self.calendar_unit
                )
                while next_due_date <= today:
                    next_due_date = self.add_calendar_interval(
                        next_due_date,
                        self.single_interval_value,
                        self.calendar_unit
                    )
                return {
                    'next_due_date': next_due_date,
                    'next_due_meter': None,
                    'step': None,
                }
            next_due_date, step = self.get_multi_step_due_calendar()
            return {
                'next_due_date': next_due_date,
                'next_due_meter': None,
                'step': step,
            }
        if self.qm_type == 'METER':
            if current_meter is None:
                current_meter = self.get_current_meter()
            avg_daily_usage = self.get_average_daily_usage()
            if self.step_type == 'SINGLE':
                if self.single_interval_value is None:
                    return {
                        'next_due_date': None,
                        'next_due_meter': None,
                        'step': None,
                    }
                interval = Decimal(self.single_interval_value)
                current_meter_dec = Decimal(current_meter)
                next_due_meter = ((current_meter_dec // interval) + 1) * interval
                next_due_date = None
                if avg_daily_usage and avg_daily_usage > 0:
                    remaining = next_due_meter - current_meter_dec
                    days = max(math.ceil(remaining / avg_daily_usage), 0)
                    next_due_date = today + timedelta(days=days)
                return {
                    'next_due_date': next_due_date,
                    'next_due_meter': next_due_meter,
                    'step': None,
                }
            next_due_meter, step = self.get_multi_step_due_meter(current_meter=current_meter)
            if next_due_meter is None:
                return {
                    'next_due_date': None,
                    'next_due_meter': None,
                    'step': None,
                }
            next_due_date = None
            if avg_daily_usage and avg_daily_usage > 0:
                remaining = next_due_meter - Decimal(current_meter)
                days = max(math.ceil(remaining / avg_daily_usage), 0)
                next_due_date = today + timedelta(days=days)
            return {
                'next_due_date': next_due_date,
                'next_due_meter': next_due_meter,
                'step': step,
            }
        return {
            'next_due_date': None,
            'next_due_meter': None,
            'step': None,
        }
    def get_work_order_trigger_date(self, current_meter=None):
        due = self.get_next_due(current_meter=current_meter)
        if due['next_due_date']:
            return due['next_due_date'] - timedelta(days=self.work_order_lead_days)
        return None
    
    @classmethod
    def get_next_number(cls):
        """Predicts the next number for UI preview."""
        year_prefix = f"Q{timezone.localdate().strftime('%y')}"
        last_qm = cls.objects.filter(
            qm_number__startswith=year_prefix
        ).order_by('-qm_number').first()

        if last_qm:
            try:
                last_num = int(last_qm.qm_number[3:])
                return f"{year_prefix}{(last_num + 1):06d}"
            except (ValueError, IndexError):
                pass 
        return f"{year_prefix}000001"
    
    def save(self, *args, **kwargs):
        if not self.qm_number:
            # Re-run the check at save time to prevent gaps/duplicates
            self.qm_number = self.get_next_number()
        super().save(*args, **kwargs)
    
class QualityMaintenanceStep(models.Model):
    CALENDAR_UNIT_CHOICES = [
        ('DAY', 'Days'),
        ('WEEK', 'Weeks'),
        ('MONTH', 'Months'),
        ('YEAR', 'Years'),
    ]
    qm = models.ForeignKey(
        QualityMaintenance,
        on_delete=models.CASCADE,
        related_name='steps'
    )
    step_order = models.PositiveIntegerField()
    interval_value = models.DecimalField(max_digits=12, decimal_places=2)
    interval_unit = models.CharField(max_length=10, choices=CALENDAR_UNIT_CHOICES, null=True, blank=True)
    step_label = models.CharField(max_length=100, blank=True)
    est_work_hours = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True)
    step_checklist = models.FileField(upload_to='qm_checklists/', null=True, blank=True)
    class Meta:
        db_table = 'planning_qualitymaintenancestep'
        ordering = ['step_order']
        unique_together = ('qm', 'step_order')
    def __str__(self):
        return f'{self.qm.qm_number} - Step {self.step_order}'
    
class QualityMaintenanceInstance(models.Model):
    STATUS_CHOICES = [
        ('FORECAST', 'Forecast'),
        ('DUE', 'Due'),
        ('TRIGGERED', 'Triggered'),
        ('COMPLETE', 'Complete'),
    ]
    qm = models.ForeignKey(
        QualityMaintenance,
        on_delete=models.CASCADE,
        related_name='instances'
    )
    step = models.ForeignKey(
        QualityMaintenanceStep,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    due_date = models.DateField(null=True, blank=True)
    due_meter = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    work_order = models.ForeignKey('work_orders.WorkOrder', null=True, blank=True, on_delete=models.SET_NULL, related_name='qm_instances')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='FORECAST')
    completed_date = models.DateField(null=True, blank=True)
    completed_meter = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'planning_qualitymaintenanceinstance'
        ordering = ['-created_at']
    def __str__(self):
        return f'{self.qm.qm_number} - {self.status}'