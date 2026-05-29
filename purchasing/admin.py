from django.contrib import admin
from .models import Purchase, PurchaseLine

class PurchaseLineInline(admin.TabularInline):
    model = PurchaseLine
    fields = ['part_number_input', 'inventory_item', 'manufacturer', 'part_description', 'qty', 'unit_price']
    
@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('purchase_number', 'purchase_type', 'date', 'bill_location', 'wo_cc', 'grand_total', 'status')
    inlines = [PurchaseLineInline]
    
@admin.register(PurchaseLine)
class PurchaseLineAdmin(admin.ModelAdmin):
    list_display = ['id', 'part_number_input', 'manufacturer', 'qty', 'unit_price'] 


def barcode_preview(self, obj):
    if obj.barcode_image:
        from django.utils.html import format_html
        return format_html('<img src="{}" style="height:50px;"/>', obj.barcode_image.url)
    return "No Barcode"

barcode_preview.short_description = 'Barcode'