from io import BytesIO
import barcode
from barcode.writer import ImageWriter
from django.core.files import File
from django.db import models, transaction
from django.utils import timezone

priority_choices = [
    ("1", "1"),
    ("2", "2"),
    ("3", "3"),
]
yesno_choices = [
    ("No", "No"),
    ("Yes", "Yes"),
]
meter_choices = [
    ("", "Select"),
    ("Engine Hours", "Engine Hours"),
    ("Odometer", "Odometer"),
    ("Power Pack Hours", "Power Pack Hours"),
    ("Power Pack Left", "Power Pack Left"),
    ("Power Pack Right", "Power Pack Right"),
    ("Impact Hours", "Impact Hours"),
    ("Impact Left", "Impact Left"),
    ("Impact Right", "Impact Right"),
    ("Operating Hours", "Operating Hours"),
]

class StatusChoices(models.Model):
    status_choice = models.CharField(max_length=20)
    def __str__(self):
        return self.status_choice
    
class WorkType(models.Model):
    work_type = models.CharField(max_length=20)
    work_description = models.CharField(max_length=100)
    def __str__(self):
        return self.work_type
    
class WorkOrder(models.Model):
    work_order = models.CharField(max_length=9, unique=True, editable=False)
    barcode_image = models.ImageField(upload_to='barcodes/', blank=True)
    equipment = models.ForeignKey(
        'equipment.Equipment',
        on_delete=models.PROTECT,
        db_column='Equipment_Number',
        related_name='work_orders'
    )
    work_type = models.ForeignKey(
        'WorkType', 
        on_delete=models.PROTECT,
        related_name='work_orders'
    )
    priority = models.CharField(max_length=1, choices=priority_choices, default="3")
    machine_oos = models.CharField(max_length=3, choices=yesno_choices, null=True, blank=True)
    hours = models.IntegerField(null=True, blank=True)
    meter = models.CharField(max_length=30, choices=meter_choices, null=True, blank=True)
    job_status = models.ForeignKey(
        'StatusChoices', 
        on_delete=models.PROTECT,
        related_name='work_orders'
    )
    date_created = models.DateTimeField(default=timezone.now)
    date_closed = models.DateTimeField(null=True, blank=True)
    # Troubleshooting
    troubleshoot_description = models.CharField(max_length=100, null=True, blank=True)
    ts_extended_description = models.TextField(null=True, blank=True)
    equipment_location = models.CharField(max_length=100, null=True, blank=True)
    ts_service_report = models.TextField(null=True, blank=True)
    # Planning
    plan_start_date = models.DateTimeField(null=True, blank=True)
    safety_instructions = models.TextField(null=True, blank=True)
    spec_requirements = models.TextField(null=True, blank=True)
    legislative = models.CharField(max_length=3, choices=yesno_choices, null=True, blank=True)
    license_req = models.CharField(max_length=3, choices=yesno_choices, null=True, blank=True)
    tools_req = models.CharField(max_length=3, choices=yesno_choices, null=True, blank=True)
    conf_space = models.CharField(max_length=3, choices=yesno_choices, null=True, blank=True)
    jha = models.CharField(max_length=3, choices=yesno_choices, null=True, blank=True)
    hot_work = models.CharField(max_length=3, choices=yesno_choices, null=True, blank=True)
    parts_wty = models.CharField(max_length=3, choices=yesno_choices, null=True, blank=True)
    work_wty = models.CharField(max_length=3, choices=yesno_choices, null=True, blank=True)
    # Repair
    est_work_hours = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True)
    repair_description = models.CharField(max_length=100, null=True, blank=True)
    repair_extended_description = models.TextField(null=True, blank=True)
    job_instructions = models.TextField(null=True, blank=True)
    attached_checklist = models.FileField(upload_to='wo_attachments/', null=True, blank=True)
    fc_system = models.ForeignKey(
        'failures.System',
        on_delete=models.PROTECT,
        db_column='system_name',
        null=True,
        blank=True
    )
    fc_component = models.ForeignKey(
        'failures.Component',
        on_delete=models.PROTECT,
        db_column='component_name',
        null=True,
        blank=True
    )
    fc_failure_mode = models.ForeignKey(
        'failures.FailureType',
        on_delete=models.PROTECT,
        db_column='failure_mode',
        null=True,
        blank=True
    )
    fc_action = models.ForeignKey(
        'failures.Action',
        on_delete=models.PROTECT,
        db_column='action_name',
        null=True,
        blank=True
    )
    repair_service_report = models.TextField(null=True, blank=True)
    class Meta:
        ordering = ['-date_created']
    def __str__(self):
        return self.work_order
    @property
    def equipment_number(self):
        return getattr(self.equipment, 'Equipment_Number', '')
    @property
    def equipment_description(self):
        return getattr(self.equipment, 'Equipment_Description', '')
    @classmethod
    @transaction.atomic
    
    def generate_work_order_number(cls):
        year = timezone.now().strftime("%y")
        prefix = f"W{year}"
        last_work_order = (
            cls.objects
            .select_for_update()
            .filter(work_order__startswith=prefix)
            .order_by('-work_order')
            .first()
        )
        if last_work_order:
            last_seq = int(last_work_order.work_order[-6:])
            next_seq = last_seq + 1
        else:
            next_seq = 1
        return f"{prefix}{next_seq:06d}"
    
    def save(self, *args, **kwargs):
        if not self.work_order:
            self.work_order = self.generate_work_order_number()
            
        if self.work_order and not self.barcode_image:
            code128 = barcode.get_barcode_class('code128')
            barcode_instance = code128(self.work_order, writer=ImageWriter())
            options = {
                'module_width': 0.4, 
                'module_height': 15.0, 
                'font_size': 8,
                'text_distance': 3.0
            }
            buffer = BytesIO()
            barcode_instance.write(buffer, options=options)
            filename = f'barcode-{self.work_order}.png'
            self.barcode_image.save(filename, File(buffer), save=False)
        super().save(*args, **kwargs)