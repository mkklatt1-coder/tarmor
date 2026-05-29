from django.db import models, transaction

CC_CHOICES = [
    ('', 'Select'),
    ('Active', 'Active'),
    ('Inactive', 'Inactive')
]
    
class CostCentre(models.Model):
    Cost_Centre = models.CharField(max_length=9, unique=True)
    Cost_Centre_Description = models.CharField(max_length=100, blank=True)
    Status = models.CharField(choices=CC_CHOICES)

    class Meta:
        ordering = ["Cost_Centre"]
        verbose_name = "Cost Centre"
        verbose_name_plural = "Cost Centres"

    def __str__(self):
        if self.Cost_Centre_Description:
            return f"{self.Cost_Centre} - {self.Cost_Centre_Description}"
        return self.Cost_Centre

    @classmethod
    @transaction.atomic
    def generate_next_cost_centre(cls):
        prefix = "G"
        last_cc = (
            cls.objects
            .select_for_update()
            .filter(Cost_Centre__startswith=prefix)
            .order_by('-Cost_Centre')
            .first()
        )
        
        if last_cc:
            try:
                last_seq = int(last_cc.Cost_Centre[1:])
                next_seq = last_seq + 1
            except ValueError:
                next_seq = 1
        else:
            next_seq = 1
            
        return f"{prefix}{next_seq:08d}"

    def save(self, *args, **kwargs):
        if not self.Cost_Centre:
            self.Cost_Centre = self.generate_next_cost_centre()
        super().save(*args, **kwargs)
    
class Facility(models.Model):
    Facility_Code = models.CharField(
        max_length=10,
        unique=True,
        help_text="This is the location code used later for shift IDs, e.g. 1800."
    )
    Facility_Name = models.CharField(max_length=60, unique=True)
    Shop_Rate = models.DecimalField(max_digits=6, decimal_places=2)
    Cost_Centre = models.ForeignKey(
        CostCentre,
        on_delete=models.PROTECT
    )
    Status = models.CharField(choices=CC_CHOICES)
    Street_Address = models.CharField(max_length=100, blank=True)
    City = models.CharField(max_length=50, blank=True)
    Province_State = models.CharField(max_length=25, blank=True)
    Country = models.CharField(max_length=25, blank=True)
    Postal_Zip_Code = models.CharField(max_length=12, blank=True)
    Contact_Name = models.CharField(max_length=60, blank=True)
    Contact_Phone_Number = models.CharField(max_length=25, blank=True)
    Email_Address = models.EmailField(blank=True)
    Additional_Information = models.TextField(blank=True)
    class Meta:
        ordering = ["Facility_Name"]
        verbose_name = "Facility"
        verbose_name_plural = "Facilities"
    def __str__(self):
        return f"{self.Facility_Code} - {self.Facility_Name}"
