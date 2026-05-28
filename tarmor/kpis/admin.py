from django.contrib import admin
from .models import FailureFrequency, MTBF

@admin.register(FailureFrequency)
class FailureFrequencyAdmin(admin.ModelAdmin):
    list_display = (
        'equipment_number', 
        'equipment_type', 
        'failure_count', 
        'equipment_hours', 
        'frequency', 
        'start_date', 
        'end_date'
    )
    
    list_filter = ('asset_type', 'equipment_type', 'start_date')
    
    search_fields = ('equipment_number', 'equipment_description')
    
    readonly_fields = ('frequency',)
    
    ordering = ('-frequency',)

@admin.register(MTBF)
class MTBFAdmin(admin.ModelAdmin):
    list_display = (
        'equipment_number', 
        'asset_type', 
        'equipment_hours', 
        'failure_count', 
        'mtbf', 
        'start_date'
    )
    
    list_filter = ('asset_type', 'equipment_type', 'start_date')
    search_fields = ('equipment_number', 'equipment_description')
    readonly_fields = ('mtbf',)
    
    ordering = ('mtbf',)