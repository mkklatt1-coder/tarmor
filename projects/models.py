from django.db import models
import datetime
from django.db.models import Sum
from decimal import Decimal
from datetime import timedelta, date

class Project(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Deferred', 'Deferred'),
        ('In-Progress', 'In-Progress'),
        ('Complete', 'Complete'),
        ('Cancelled', 'Cancelled'),
    ]
    
    project_number = models.CharField(max_length=50, unique=True, blank=True)
    description = models.CharField(max_length=255)
    moc_number = models.CharField(max_length=100, blank=True)
    assigned_to = models.CharField(max_length=100, blank=True)
    start_year = models.CharField(max_length=4, blank=True)
    
    execution_time = models.IntegerField(default=1, blank=True, null=True)
    uom = models.CharField(max_length=20, default='Years', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending', blank=True, null=True)
    
    budget = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, blank=True, null=True)
    spend = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, blank=True, null=True)
    remaining = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, blank=True, null=True)

    scope = models.TextField(blank=True)
    justification = models.TextField(blank=True)

    def __str__(self):
        return f"{self.project_number} - {self.description}"

    @property
    def completion_percentage(self):
        steps = self.steps.all()
        if not steps:
            return "0%"
        completed = steps.filter(status__iexact='Complete').count()
        percentage = (completed / steps.count()) * 100
        return f"{int(percentage)}%"
    
    def save(self, *args, **kwargs):
        if not self.project_number:
            year_suffix = str(datetime.datetime.now().year)[2:]
            prefix = f"X{year_suffix}"
            
            last_project = Project.objects.filter(project_number__startswith=prefix).order_by('project_number').last()
            
            if last_project:
                last_seq = int(last_project.project_number[-6:])
                new_seq = str(last_seq + 1).zfill(6)
            else:
                new_seq = "000001"
                
            self.project_number = f"{prefix}{new_seq}"
            pass
        super().save(*args, **kwargs)

    def update_totals(self):
        from django.db.models import Sum
        total_budget = self.budgets.aggregate(Sum('allocated_budget'))['allocated_budget__sum'] or Decimal('0.00')
        total_spent = self.purchase_orders.aggregate(Sum('grand_total'))['grand_total__sum'] or Decimal('0.00')
        
        self.budget = total_budget
        self.spend = total_spent
        self.remaining = self.budget - self.spend
        
        Project.objects.filter(pk=self.pk).update(
            budget=self.budget,
            spend=self.spend,
            remaining=self.remaining
        )

    @property
    def ve_ratio(self):
        from moc.models import MOC
        
        moc = MOC.objects.filter(moc_number=self.moc_number).first()
        
        if moc:
            point = moc.effval.first() 
            return point.ratio if point else "-"
        return "-"
    
class ProjectStep(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='steps')
    step_number = models.IntegerField()
    description = models.CharField(max_length=255)
    time_to_implement = models.IntegerField()
    uom = models.CharField(max_length=20)
    start_date = models.DateField()
    status = models.CharField(max_length=50)

    def __str__(self):
        return f"Step {self.step_number}: {self.description}"
    
    def get_duration_days(self):
        """Converts UOM to days."""
        val = self.time_to_implement
        uom = self.uom.lower()
        if 'week' in uom: return val * 7
        if 'month' in uom: return val * 30
        return val

    def get_end_date(self):
        return self.start_date + timedelta(days=self.get_duration_days())

    def get_delay_days(self):
        """Sums all linked delays for this step."""
        total = 0
        for d in self.project.delays.filter(step=self):
            val = d.time_requirement
            uom = d.uom.lower()
            if 'week' in uom: total += (val * 7)
            elif 'month' in uom: total += (val * 30)
            else: total += val
        return total

    def get_final_date(self):
        return self.get_end_date() + timedelta(days=self.get_delay_days())

class ProjectDelay(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='delays')
    step = models.ForeignKey(ProjectStep, on_delete=models.CASCADE)
    delay_type = models.CharField(max_length=100)
    cause = models.CharField(max_length=100)
    time_requirement = models.IntegerField()
    uom = models.CharField(max_length=20)

class ProjectAttachment(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='attachments')
    name = models.CharField(max_length=100)
    file = models.FileField(upload_to='project_attachments/')

class ProjectBudget(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='budgets')
    year = models.IntegerField()
    allocated_budget = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    @property
    def yearly_spend(self):
        spend = self.project.purchase_orders.filter(
            date__year=self.year
        ).aggregate(Sum('grand_total'))['grand_total__sum']
        
        return spend or Decimal('0.00') 

    @property
    def yearly_remaining(self):
        return self.allocated_budget - self.yearly_spend
    
class ProjectNote(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='notes')
    step = models.ForeignKey(ProjectStep, on_delete=models.SET_NULL, null=True, blank=True)
    
    date = models.DateField(default=datetime.date.today)
    step_note = models.CharField(max_length=255, blank=True)
    action = models.TextField(blank=True)
    due_date = models.DateField(null=True, blank=True)
    progress = models.TextField(blank=True)
    completed_date = models.DateField(null=True, blank=True)
    complete = models.CharField(max_length=10, choices=[('Yes', 'Yes'), ('No', 'No')], default='No')

    def __str__(self):
        return f"Note for {self.project.project_number}"
    
class ProjectLesson(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='lessons')
    step = models.ForeignKey(ProjectStep, on_delete=models.SET_NULL, null=True, blank=True)
    
    date = models.DateField(default=datetime.date.today)
    failure = models.CharField(max_length=255, blank=True)
    action = models.TextField(blank=True)
    lesson = models.CharField(max_length=255, blank=True)
    progress = models.TextField(blank=True)
    completed_date = models.DateField(null=True, blank=True)
    complete = models.CharField(max_length=10, choices=[('Yes', 'Yes'), ('No', 'No')], default='No')

    def __str__(self):
        return f"Lesson for {self.project.project_number}"
    
class ProjectFinancial(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='financials')
    year = models.IntegerField()

    jan_p = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    feb_p = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    mar_p = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    apr_p = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    may_p = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    jun_p = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    jul_p = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    aug_p = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    sep_p = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    oct_p = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    nov_p = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    dec_p = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cost_carryover = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cash_carryover = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def get_monthly_data(self, month_num, type='cost'):
        """
        type='cost': PO status != 'Complete'
        type='cash': PO status == 'Complete'
        """
        qs = self.project.purchase_orders.filter(date__year=self.year, date__month=month_num)
        if type == 'cash':
            qs = qs.filter(status='Complete')
        else:
            qs = qs.exclude(status='Complete')
        
        return qs.aggregate(Sum('grand_total'))['grand_total__sum'] or Decimal('0.00')

    @property
    def planned_total(self):
        months = [
            self.jan_p, self.feb_p, self.mar_p, self.apr_p, self.may_p, self.jun_p,
            self.jul_p, self.aug_p, self.sep_p, self.oct_p, self.nov_p, self.dec_p
        ]
        return sum(filter(None, months))
    
    def _get_sum(self, month, is_cash):
        qs = self.project.purchase_orders.filter(date__year=self.year, date__month=month)
        if is_cash:
            qs = qs.filter(status='Complete')
            val = qs.aggregate(Sum('grand_total'))['grand_total__sum'] or Decimal('0.00')
            if month == 1:
                prev = ProjectFinancial.objects.filter(project=self.project, year=self.year-1).first()
                if prev: val += prev.cash_carryover
        else:
            qs = qs.exclude(status='Complete')
            val = qs.aggregate(Sum('grand_total'))['grand_total__sum'] or Decimal('0.00')
            if month == 1:
                prev = ProjectFinancial.objects.filter(project=self.project, year=self.year-1).first()
                if prev: val += prev.cost_carryover
        return val

    @property
    def jan_cost(self): return self._get_sum(1, False)
    @property
    def feb_cost(self): return self._get_sum(2, False)
    @property
    def mar_cost(self): return self._get_sum(3, False)
    @property
    def apr_cost(self): return self._get_sum(4, False)
    @property
    def may_cost(self): return self._get_sum(5, False)
    @property
    def jun_cost(self): return self._get_sum(6, False)
    @property
    def jul_cost(self): return self._get_sum(7, False)
    @property
    def aug_cost(self): return self._get_sum(8, False)
    @property
    def sep_cost(self): return self._get_sum(9, False)
    @property
    def oct_cost(self): return self._get_sum(10, False)
    @property
    def nov_cost(self): return self._get_sum(11, False)
    @property
    def dec_cost(self): return self._get_sum(12, False)

    # Cash Properties (Status == Complete)
    @property
    def jan_cash(self): return self._get_sum(1, True)
    @property
    def feb_cash(self): return self._get_sum(2, True)
    @property
    def mar_cash(self): return self._get_sum(3, True)
    @property
    def apr_cash(self): return self._get_sum(4, True)
    @property
    def may_cash(self): return self._get_sum(5, True)
    @property
    def jun_cash(self): return self._get_sum(6, True)
    @property
    def jul_cash(self): return self._get_sum(7, True)
    @property
    def aug_cash(self): return self._get_sum(8, True)
    @property
    def sep_cash(self): return self._get_sum(9, True)
    @property
    def oct_cash(self): return self._get_sum(10, True)
    @property
    def nov_cash(self): return self._get_sum(11, True)
    @property
    def dec_cash(self): return self._get_sum(12, True)
    
    @property
    def cost_total(self):
        return sum([self.jan_cost, self.feb_cost, self.mar_cost, self.apr_cost, self.may_cost, self.jun_cost, 
                    self.jul_cost, self.aug_cost, self.sep_cost, self.oct_cost, self.nov_cost, self.dec_cost])

    @property
    def cash_total(self):
        return sum([self.jan_cash, self.feb_cash, self.mar_cash, self.apr_cash, self.may_cash, self.jun_cash, 
                    self.jul_cash, self.aug_cash, self.sep_cash, self.oct_cash, self.nov_cash, self.dec_cash])
    
class ProjectTasks(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    step = models.ForeignKey(ProjectStep, on_delete=models.SET_NULL, null=True, blank=True)
    
    date = models.DateField(default=datetime.date.today)
    tasks = models.CharField(max_length=255, blank=True)
    assignee = models.CharField(max_length=255, blank=True)
    due_date = models.DateField(null=True, blank=True)
    progress = models.TextField(blank=True)
    completed_date = models.DateField(null=True, blank=True)
    complete = models.CharField(max_length=10, choices=[('Yes', 'Yes'), ('No', 'No')], default='No')

    def __str__(self):
        return f"Tasks for {self.project.project_number}"
    
class CompanyBudget(models.Model):
    year = models.IntegerField(unique=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.year}: ${self.amount}"
    
    @property
    def safety_score(self):
        from moc.models import MOCConsiderations
        moc = MOCConsiderations.objects.filter(moc__moc_number=self.moc_number).first()
        return moc.risk_total_value if moc else "-"

    @property
    def ve_ratio(self):
        from moc.models import MOCEffValPoint
        point = MOCEffValPoint.objects.filter(moc__moc_number=self.moc_number).first()
        return point.ratio if point else "-"