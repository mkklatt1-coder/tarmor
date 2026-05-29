from django.db import models
from localflavor.ca.ca_provinces import PROVINCE_CHOICES
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator

status_choices=[
    ('Active', 'Active'),
    ('Inactive', 'Inactive')
]

class Supplier(models.Model):
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Format: '+999999999'"
    )
    supplier_name = models.CharField(max_length=255)
    status = models.CharField(choices=status_choices)
    street_address = models.CharField(max_length=255)
    city = models.CharField(max_length=50)
    province_state = models.CharField(max_length=2, choices=PROVINCE_CHOICES)
    country = models.CharField(max_length=100, null=True, blank=True)
    postal_zip = models.CharField(max_length=10, null=True, blank=True)
    contact = models.CharField(max_length=50)
    phone = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    email = models.EmailField(max_length=255, null=True, blank=True, unique=True)
    supplier_discount = models.DecimalField(
        max_digits=5, 
        decimal_places=4, 
        default=0.0000,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Enter discount as a decimal (e.g., 0.15 for 15%)"
    )
    payment_method = models.CharField(max_length=100, null=True, blank=True)
    supplier_currency = models.CharField(max_length=4, null=True, blank=True)
    additional_information = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.supplier_name}"

    @property
    def discount_percentage(self):
        """Helper to show the human-readable percentage"""
        return self.supplier_discount * 100