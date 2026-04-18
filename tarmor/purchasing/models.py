from decimal import Decimal
from django.db import models, transaction
from django.db.models import Sum
from django.utils import timezone
from inventory.models import InventoryItem
from work_orders.models import WorkOrder
from facilities.models import CostCentre
from suppliers.models import Supplier
from io import BytesIO
import barcode
from barcode.writer import ImageWriter
from django.core.files import File

purchase_type_choices = [
    ('P', 'Purchase Order'),
    ('R', 'Purchase Requisition'),
    ('S', 'Service Order'),
]
billing_choices = [
    ('Work Order', 'Work Order'),
    ('Cost Centre', 'Cost Centre'),
]
status_choices = [
    ("Pending", "Pending"),
    ("Shipped", "Shipped"),
    ("Received", "Received"),
    ("Cancelled", "Cancelled"),
    ("Returned", "Returned"),
    ("Paid", "Paid"),
]
class Purchase(models.Model):
    purchase_type = models.CharField(max_length=1, choices=purchase_type_choices)
    purchase_number = models.CharField(max_length=9, unique=True, blank=True)
    barcode_image = models.ImageField(upload_to='barcodes/', blank=True, editable=False)
    date = models.DateField(default=timezone.now)
    bill_location = models.CharField(max_length=20, choices=billing_choices)
    wo_cc = models.CharField(max_length=50)
    grand_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=10, choices=status_choices, default="Pending")
    additional_information = models.TextField(null=True, blank=True)
    class Meta:
        ordering = ['-id']
    def __str__(self):
        return self.purchase_number
    
    def generate_purchase_number(self):
        prefix = self.purchase_type
        year = timezone.now().strftime('%y')
        last_item = (
            Purchase.objects
            .select_for_update()
            .filter(purchase_number__startswith=f"{prefix}{year}")
            .order_by('purchase_number')
            .last()
        )
        if last_item:
            last_no = int(last_item.purchase_number[3:])
            next_no = str(last_no + 1).zfill(6)
        else:
            next_no = "000001"
        return f"{prefix}{year}{next_no}"
    
    def update_grand_total(self):
        total = self.lines.aggregate(total=Sum('total_price'))['total'] or Decimal('0.00')
        self.grand_total = total
        Purchase.objects.filter(pk=self.pk).update(grand_total=total)
        
    def save(self, *args, **kwargs):
        if not self.purchase_number:
            with transaction.atomic():
                self.purchase_number = self.generate_purchase_number()
            
        if self.purchase_number and not self.barcode_image:
            code128 = barcode.get_barcode_class('code128')
            barcode_instance = code128(self.purchase_number, writer=ImageWriter())
            options = {
                'module_width': 0.4, 
                'module_height': 15.0, 
                'font_size': 8,
                'text_distance': 3.0
            }
            buffer = BytesIO()
            barcode_instance.write(buffer, options=options)
            buffer.seek(0) 
            filename = f'barcode-{self.purchase_number}.png'
            self.barcode_image.save(filename, File(buffer), save=False)
            super().save(*args, **kwargs)
            
    @property
    def wo_cc_display(self):
        """Returns the actual WO or CC value instead of the ID"""
        if not self.wo_cc:
            return ""
        try:
            if self.bill_location == 'Work Order':
                return WorkOrder.objects.get(work_order=self.wo_cc).work_order
            elif self.bill_location == 'Cost Centre':
                return CostCentre.objects.get(Cost_Centre=self.wo_cc).Cost_Centre
        except (WorkOrder.DoesNotExist, CostCentre.DoesNotExist):
            return self.wo_cc
        
        return self.wo_cc
        
        
class PurchaseLine(models.Model):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='lines')
    part_number_input = models.CharField(max_length=100)
    manual_part_number = models.CharField(max_length=100, blank=True) 
    inventory_item = models.ForeignKey(
        InventoryItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    manufacturer = models.CharField(max_length=255, blank=True)
    part_description = models.CharField(max_length=255, blank=True)
    uom = models.CharField(max_length=30, blank=True)
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    qty = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('1.00'))
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), editable=False)
    row_status = models.CharField(max_length=10, choices=status_choices, default="Pending")
   
    def save(self, *args, **kwargs):
        if self.purchase.purchase_type == 'R' and self.part_number_input and self.manufacturer:
            item = InventoryItem.objects.filter(
                part_number__iexact=self.part_number_input,
                manufacturer__iexact=self.manufacturer
            ).first()
            
            if self.inventory_item:
                self.part_number_input = self.inventory_item.part_number
                self.manufacturer = self.inventory_item.manufacturer
                self.supplier = self.inventory_item.supplier
                
                if not self.unit_price:
                    self.unit_price = self.inventory_item.unit_price
                    
        self.total_price = (self.qty or 0) * (self.unit_price or 0)
        super().save(*args, **kwargs)