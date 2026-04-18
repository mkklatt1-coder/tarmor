from django.contrib import admin
from .models import Supplier

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('supplier_name', 'status', 'street_address', 'city', 'province_state', 'country', 'postal_zip', 'contact', 
                    'phone', 'email', 'supplier_discount', 'payment_method', 'supplier_currency')
    search_fields = ('supplier_name', 'status')