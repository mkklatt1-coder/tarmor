from django.db import models
from django.core.validators import RegexValidator
import calendar
import holidays
from datetime import date, datetime, timedelta
import uuid

STATUS_CHOICES = [
    ('Active', 'Active'),
    ('Inactive', 'Inactive'),
]

YESNO_CHOICES = [
    ('No', 'No'),
    ('Yes', 'Yes'),
]
    
PROVINCE_CHOICES = [
    ('AB', 'Alberta'), ('BC', 'British Columbia'), ('MB', 'Manitoba'),
    ('NB', 'New Brunswick'), ('NL', 'Newfoundland and Labrador'),
    ('NS', 'Nova Scotia'), ('NT', 'Northwest Territories'),
    ('NU', 'Nunavut'), ('ON', 'Ontario'), ('PE', 'Prince Edward Island'),
    ('QC', 'Quebec'), ('SK', 'Saskatchewan'), ('YT', 'Yukon'),
]

class ShiftPattern(models.Model):
    name = models.CharField(max_length=100)
    pattern_sequence = models.CharField(
        max_length=100, 
        help_text="Comma-separated days: 5,5,4,4 (Work 5, Off 5, Work 4, Off 4)"
    )
    is_rotating = models.BooleanField(default=True)

    def get_steps(self):
        """Returns the raw integers, e.g., [5, 5, 4, 4]"""
        return [int(x.strip()) for x in self.pattern_sequence.split(',')]
    
    def get_required_crews(self, coverage_type):
        """Returns 4 for 24H, 2 for DS/NS, and 1 for 5,2 patterns."""
        if coverage_type == "24H":
            return 4
        elif coverage_type in ["DS", "NS"]:
            # If it's a 5,2 pattern, we only need 1 crew for that specific shift
            if self.pattern_sequence == "5,2":
                return 1
            return 2
        return 1
    
    def get_pattern_list(self):
        steps = [int(x.strip()) for x in self.pattern_sequence.split(',')]
        full_cycle = []
        is_on = True
        for count in steps:
            full_cycle.extend([is_on] * count)
            is_on = not is_on
        return full_cycle

    @property
    def cycle_length(self):
        return len(self.get_pattern_list())
    
    def __str__(self):
        return f"{self.name} ({self.pattern_sequence})"

    def get_stagger_interval(self):
        """
        Calculates the offset for the next crew.
        For '5,5,4,4', the first crew works 5 days, so the next starts on Day 6.
        """
        steps = [int(x.strip()) for x in self.pattern_sequence.split(',')]
        return steps[0]
    
class CrewShiftRotation(models.Model):
    COVERAGE_TYPE_CHOICES = [
        ("24H", "24 Hour Coverage"),
        ("DS", "Day Shift Only"),
        ("NS", "Night Shift Only"),
    ]
    
    CALENDAR_MONTH_CHOICES = [
        ("January", "January"),
        ("February", "February"),
        ("March", "March"),
        ("April", "April"),
        ("May", "May"),
        ("June", "June"),
        ("July", "July"),
        ("August", "August"),
        ("September", "September"),
        ("October", "October"),
        ("November", "November"),
        ("December", "December"),
    ]
    
    Shift_ID = models.CharField(max_length=20, unique=True, editable=False)
    Location = models.ForeignKey("facilities.Facility",on_delete=models.PROTECT)
    Coverage_Type = models.CharField(max_length=3, choices=COVERAGE_TYPE_CHOICES)
    hrs_per_shift = models.CharField(max_length=2)
    shift_start = models.TimeField(null=True, blank=True, help_text="Format HH:MM (e.g. 07:00 or 19:00)")
    Calendar_Month = models.CharField(max_length=15, choices=CALENDAR_MONTH_CHOICES, default="January")
    Start_Date = models.DateField()
    pattern = models.ForeignKey(ShiftPattern, on_delete=models.PROTECT, null=True)
    province = models.CharField(max_length=2, choices=PROVINCE_CHOICES, default='MB')
    batch_id = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def generate_shift_id(self):
        prefix = str(self.Location.Facility_Code).rstrip("-")
        last_sequence = -1
        existing_ids = (
            CrewShiftRotation.objects
            .filter(Location=self.Location)
            .exclude(pk=self.pk)
            .values_list("Shift_ID", flat=True)
        )
        for shift_id in existing_ids:
            if not shift_id or "-" not in shift_id:
                continue
            suffix = shift_id.split("-", 1)[1]
            last_sequence = max(last_sequence, index_from_alpha(suffix))
        
        next_suffix = alpha_from_index(last_sequence + 1)
        return f"{prefix}-{next_suffix}"
    
    def save(self, *args, **kwargs):
        if not self.Shift_ID and self.Location_id:
            self.Shift_ID = self.generate_shift_id()
        super().save(*args, **kwargs)
        
        if self.Location and self.Shift_ID:
            Crew.objects.update_or_create(
                location_code=str(self.Location.Facility_Code),
                shift_letter=self.Shift_ID.split('-')[-1],
                defaults={
                    'pattern': self.pattern,
                    'start_date': self.Start_Date,
                    'province': self.province
                }
            )

class Crew(models.Model):
    location_code = models.CharField(max_length=50) 
    shift_letter = models.CharField(max_length=1)
    pattern = models.ForeignKey(ShiftPattern, on_delete=models.PROTECT, related_name="crews")
    start_date = models.DateField()
    rotation = models.ForeignKey('CrewShiftRotation', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_crews')
    province = models.CharField(max_length=2, choices=PROVINCE_CHOICES, default='MB')

    def get_status_for_date(self, target_date):
        """
        Determines if a crew is DAY, NIGHT, or OFF based on their specific 
        rotation block and their initial shift_start time.
        """
        if not self.pattern or not self.start_date:
            return "OFF"
        
        steps = self.pattern.get_steps() # e.g. [5, 5, 4, 4]
        cycle_length = sum(steps)
        delta = (target_date - self.start_date).days

        if delta < 0:
            return "OFF"

        day_in_cycle = delta % cycle_length

        running_total = 0
        block_index = -1
        for i, step_count in enumerate(steps):
            running_total += step_count
            if day_in_cycle < running_total:
                block_index = i
                break

        if block_index % 2 != 0 or block_index == -1:
            return "OFF"
    
        starts_on_nights = False
        if self.rotation and self.rotation.shift_start:
            if self.rotation.shift_start.hour >= 16:
                starts_on_nights = True

        if starts_on_nights:
            return "NIGHT" if block_index % 4 == 0 else "DAY"
        else:
            return "DAY" if block_index % 4 == 0 else "NIGHT"       
    
    def get_calendar_data(self, year):
        prov = getattr(self.rotation, 'province', 'MB')
        ca_holidays = holidays.Canada(subdiv=prov, years=year)
        steps = self.pattern.get_steps()  # e.g., [5, 5, 4, 4]
        cycle_length = sum(steps)

        all_months = []

        for month in range(1, 13):
            month_weeks = []
            cal = calendar.monthcalendar(year, month)
            
            for week in cal:
                week_days = []
                for day in week:
                    if day == 0:
                        week_days.append(None)
                    else:
                        current_date = date(year, month, day)
                        delta = (current_date - self.start_date).days
                        
                        if delta < 0:
                            shift_type = 'OFF'
                        else:
                            day_in_cycle = delta % cycle_length
                            shift_type = self.determine_rotating_shift(day_in_cycle, steps)

                        is_holiday = current_date in ca_holidays
                        
                        week_days.append({
                            'day': day,
                            'shift_type': shift_type,
                            'is_holiday': is_holiday,
                            'holiday_name': ca_holidays.get(current_date) if is_holiday else ""
                        })
                month_weeks.append(week_days)
            all_months.append({'name': calendar.month_name[month], 'weeks': month_weeks})
        return all_months
    
    def determine_rotating_shift(self, day_in_cycle, steps):
        running_total = 0
        block_index = -1

        for i, step_count in enumerate(steps):
            running_total += step_count
            if day_in_cycle < running_total:
                block_index = i
                break

        if block_index % 2 != 0 or block_index == -1:
            return 'OFF'
        
        starts_on_nights = False
        if self.rotation and self.rotation.shift_start:
            if self.rotation.shift_start.hour >= 16:
                starts_on_nights = True

        if starts_on_nights:
            return 'NIGHT' if block_index % 4 == 0 else 'DAY'
        else:
            return 'DAY' if block_index % 4 == 0 else 'NIGHT'
    
    @property
    def full_shift_id(self):
        return f"{self.location_code}-{self.shift_letter}"
    full_shift_id.fget.short_description = "Shift ID"
    
    def __str__(self):
        return f"{self.location_code}-{self.shift_letter}"
        
class Employee(models.Model):
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Format: '+999999999'"
    )
    crew = models.ForeignKey(Crew, on_delete=models.SET_NULL, null=True, blank=True, related_name="members")
    First_Name = models.CharField(max_length=255)
    Middle_Name = models.CharField(max_length=255, blank=True)
    Last_Name = models.CharField(max_length=255)
    Status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    Position = models.CharField(max_length=255)
    Start_Date = models.DateField(null=True, blank=True)
    Last_Date = models.DateField(null=True, blank=True)
    Street_Address = models.CharField(max_length=255, null=True, blank=True)
    City = models.CharField(max_length=100, null=True, blank=True)
    Prov_State = models.CharField(max_length=50, choices=PROVINCE_CHOICES, null=True, blank=True)
    Country = models.CharField(max_length=100, null=True, blank=True)
    Postal_Zip = models.CharField(max_length=10, null=True, blank=True)
    Phone = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    Email = models.EmailField(max_length=255, null=True, blank=True, unique=True)
    EC_First_Name = models.CharField(max_length=255)
    EC_Middle_Name = models.CharField(max_length=255, blank=True)
    EC_Last_Name = models.CharField(max_length=255)
    EC_Phone = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    EC_Email = models.EmailField(max_length=255, null=True, blank=True)
    Additional_Information = models.TextField(blank=True)
    Employee_Image = models.ImageField(upload_to='employee_pics/', null=True, blank=True)
    
    def __str__(self):
        return f"{self.First_Name} {self.Last_Name}"
    
class EmployeeCertification(models.Model):
    Employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='certifications'
    )
    Certification = models.CharField(max_length=255, null=True, blank=True)
    Institution = models.CharField(max_length=255, null=True, blank=True)
    Date_Cert = models.DateField(null=True, blank=True)
    Renewable = models.CharField(max_length=6, choices=YESNO_CHOICES, default='No')
    Renewal_Cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    def __str__(self):
        cert_name = self.Certification or "Certification"
        return f"{self.Employee} - {cert_name}"
 
def alpha_from_index(index):
    """
    0 -> A
    1 -> B
    25 -> Z
    26 -> AA
    """
    index += 1
    value = ""
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        value = chr(65 + remainder) + value
    return value

def index_from_alpha(value):
    """
    A -> 0
    B -> 1
    Z -> 25
    AA -> 26
    """
    total = 0
    for char in value.upper():
        total = (total * 26) + (ord(char) - 64)
    return total - 1


        
