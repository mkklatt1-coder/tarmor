from django.db import models
from suppliers.models import Supplier
from django.utils import timezone

stock_choices=[
    ('Stock', 'Stock'),
    ('Non-Stock', 'Non-Stock')
]

yesno_choices = [
    ("No", "No"),
    ("Yes", "Yes"),
]

class InventoryItem(models.Model):
    part_number = models.CharField(max_length=20)
    part_description = models.CharField(max_length=255)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, db_column='supplier_name')
    manufacturer = models.CharField(max_length=255, null=True, blank=True)
    qty = models.IntegerField()
    uom = models.CharField(max_length=10)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.CharField(max_length=10, choices=stock_choices)
    controlled_product = models.CharField(max_length=3, choices=yesno_choices)
    bin_location = models.CharField(max_length=50)
    qty_onhand = models.IntegerField()
    min_qty = models.IntegerField()
    max_qty = models.IntegerField()
    last_transaction_date = models.DateField(default=timezone.now)
    last_transaction_number = models.CharField(max_length=10)
    alternatives = models.ManyToManyField('self', blank=True, symmetrical=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['part_number', 'manufacturer'], 
                name='unique_part_manufacturer'
            )
        ]

    def __str__(self):
        return f"{self.manufacturer} {self.part_number}"
  
    
    