from django.contrib import admin
from .models import InventoryItem

@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ('part_number', 'part_description', 'supplier', 'manufacturer', 'qty', 'uom', 'unit_price', 'stock', 'controlled_product')
    list_filter = ('supplier', 'manufacturer', 'controlled_product')
    search_fields = ('part_number', 'part_description', 'supplier__supplier_name', 'manufacturer')


