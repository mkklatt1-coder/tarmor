from django.db import models
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from moc.services.effval import calculate_effval

def generate_moc_number():
    year = timezone.now().strftime("%y")
    last = MOC.objects.filter(moc_number__startswith=f"M{year}").order_by("moc_number").last()
    if not last:
        return f"M{year}000001"
    seq = int(last.moc_number[-6:]) + 1
    return f"M{year}{seq:06d}"

RISK_CHOICES = [
    ("0", "0"),
    ("5", "5"),
    ("10", "10"),
    ("25", "25"),
    ("35", "35"),
    ("50", "50"),
]
FREQ_CHOICES = [
    ("0", "0"),
    ("2", "2"),
    ("4", "4"),
    ("6", "6"),
    ("8", "8"),
    ("10", "10"),
]
YESNO_CHOICES = [
    ("Yes", "Yes"),
    ("No", "No"),
    ("N/A", "N/A"),
]
STATUS_CHOICES = [
    ("Pending", "Pending"),
    ("Approved", "Approved"),
    ("Rejected", "Rejected"),
    ("Deferred", "Deferred"),
    ("In Progress", "In Progress"),
    ("Cancelled", "Cancelled"),
    ("Completed", "Completed"),
]
class MOC(models.Model):
    moc_number = models.CharField(max_length=12, unique=True, default=generate_moc_number)
    title = models.CharField(max_length=255)
    date_created = models.DateField(auto_now_add=True)
    date_completed = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, blank=True)
    define_change = models.TextField(blank=True)
    anticipated_outcome = models.TextField(blank=True)

    def __str__(self):
        return self.moc_number
    
@receiver(post_save, sender=MOC)
def update_moc_scores(sender, instance, **kwargs):
    calculate_effval(instance)

class MOCPro(models.Model):
    moc = models.ForeignKey(MOC, on_delete=models.CASCADE, related_name="pros")
    text = models.CharField(max_length=500, null=True, blank=True)

class MOCCon(models.Model):
    moc = models.ForeignKey(MOC, on_delete=models.CASCADE, related_name="cons")
    text = models.CharField(max_length=500, null=True, blank=True)

class MOCAttachment(models.Model):
    moc = models.ForeignKey(MOC, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to="moc_attachments/")
    description = models.CharField(max_length=255, null=True, blank=True)

SETUP_CHOICES = [
    ("0-6", "0-6"),
    ("7-12", "7-12"),
    ("13-18", "13-18"),
    ("19-24", "19-24"),
    (">24", ">24"),
]
IMPLEMENT_CHOICES = [
    ("0-3", "0-3"),
    ("4-6", "4-6"),
    ("7-9", "7-9"),
    ("10-12", "10-12"),
    (">12", ">12"),
]
VALUE_CHOICES = [
    ("None", "None"),
    ("Low", "Low"),
    ("Med", "Med"),
    ("High", "High"),
]
CONT_HOURS_CHOICES = [
    ("0-50", "0-50"),
    ("51-100", "51-100"),
    ("101-200", "101-200"),
    ("201-300", "201-300"),
    (">300", ">300"),
]
PROJ_COST_CHOICES = [
    ("0", "0"),
    ("1-5000", "1-5000"),
    ("5001-10000", "5001-10000"),
    ("10001-50000", "10001-50000"),
    (">50000", ">50000"),
]
SAVINGS_CHOICES = [
    ("0-10000", "0-10000"),
    ("10001-50000", "10001-50000"),
    ("50001-75000", "50001-75000"),
    ("75001-100000", "75001-100000"),
    (">100000", ">100000"),
]
PROD_CHOICES = [
    ("0-5", "0-5"),
    ("6-10", "6-10"),
    ("11-15", "11-15"),
    ("16-20", "16-20"),
    (">20", ">20"),
]
class MOCConsiderations(models.Model):
    moc = models.OneToOneField(MOC, on_delete=models.CASCADE, related_name="considerations")
    setup_months = models.CharField(max_length=10, choices=SETUP_CHOICES, blank=True)
    implementation_months = models.CharField(max_length=10, choices=IMPLEMENT_CHOICES, blank=True)
    contractor_hours = models.CharField(max_length=12, choices=CONT_HOURS_CHOICES, blank=True)
    eq_downtime = models.CharField(max_length=10, choices=SETUP_CHOICES, blank=True)
    warranty_impact = models.CharField(max_length=10, choices=VALUE_CHOICES, blank=True)
    project_cost = models.CharField(max_length=20, choices=PROJ_COST_CHOICES, blank=True)
    savings_confirmed = models.CharField(max_length=20, choices=SAVINGS_CHOICES, blank=True)
    savings_soft = models.CharField(max_length=20, choices=SAVINGS_CHOICES, blank=True)
    inventory_cost = models.CharField(max_length=20, choices=PROJ_COST_CHOICES, blank=True)
    production_gain = models.CharField(max_length=20, choices=PROD_CHOICES, blank=True)
    safety_gain = models.CharField(max_length=10, choices=VALUE_CHOICES, blank=True)
    social_impact = models.CharField(max_length=10, choices=VALUE_CHOICES, blank=True)
    roi_months = models.CharField(max_length=10, choices=IMPLEMENT_CHOICES, blank=True)

class MOCEffValPoint(models.Model):
    moc = models.ForeignKey(MOC, on_delete=models.CASCADE, related_name="effval")
    effort = models.FloatField()
    value = models.FloatField()
    ratio = models.FloatField(null=True, blank=True)

class Safety(models.Model):
    moc = models.OneToOneField(MOC, on_delete=models.CASCADE, related_name="safety")
    sh_risk = models.CharField(max_length=4, choices=RISK_CHOICES, blank=True)
    sh_freq = models.CharField(max_length=4, choices=FREQ_CHOICES, blank=True)
    env_risk = models.CharField(max_length=4, choices=RISK_CHOICES, blank=True)
    env_freq = models.CharField(max_length=4, choices=FREQ_CHOICES, blank=True)
    fin_risk = models.CharField(max_length=4, choices=RISK_CHOICES, blank=True)
    fin_freq = models.CharField(max_length=4, choices=FREQ_CHOICES, blank=True)
    soc_risk = models.CharField(max_length=4, choices=RISK_CHOICES, blank=True)
    soc_freq = models.CharField(max_length=4, choices=FREQ_CHOICES, blank=True)

    @property
    def risk_total_value(self):
        def v(x):
            return int(x) if x and x.isdigit() else 0
        return (
            v(self.sh_risk) * v(self.sh_freq)
            + v(self.env_risk) * v(self.env_freq)
            + v(self.fin_risk) * v(self.fin_freq)
            + v(self.soc_risk) * v(self.soc_freq)
        )
    
SECTION_CHOICES = [
    ('safety', 'Safety & Health'),
    ("documentation", "Documentation"),
    ("education", "Education"),
    ("procurement", "Procurement"),
    ("data_tech", "Data & Technology"),
    ("test_imp", "Test & Implementation"),
    ("social", "Social"),
]
class MOCQuestion(models.Model):
    section = models.CharField(max_length=30, choices=SECTION_CHOICES)
    text = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.section} | {self.text}"
    
class MOCQuestionResponse(models.Model):
    moc = models.ForeignKey(MOC, on_delete=models.CASCADE, related_name="responses")
    question = models.ForeignKey(MOCQuestion, on_delete=models.CASCADE, related_name="responses")
    dropdown_answer = models.CharField(max_length=6, choices=YESNO_CHOICES)
    detail = models.TextField(blank=True)
    complete = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.moc.moc_number} | {self.question.text}"

class EffValRule(models.Model):
    EFFORT = "EFFORT"
    VALUE = "VALUE"
    CATEGORY_CHOICES = [
        (EFFORT, "Effort"),
        (VALUE, "Value"),
    ]
    name = models.CharField(max_length=50)
    label = models.CharField(max_length=100)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
    source_field = models.CharField(max_length=50)
    weight = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f"{self.label} ({self.category})"
    
class EffValPointRange(models.Model):
    rule = models.ForeignKey(EffValRule, on_delete=models.CASCADE, related_name="ranges")
    value_key = models.CharField(max_length=20)
    points = models.IntegerField()

    class Meta:
        ordering = ["value_key"]

@receiver(post_save, sender=MOC)
def update_effval_on_save(sender, instance, **kwargs):
    calculate_effval(instance)