from django.contrib import admin
from .models import MeterReading

@admin.register(MeterReading)
class MeterReadingAdmin(admin.ModelAdmin):
    list_display = ('Date', 'Equipment', 'Meter_Type', 'Meter_Reading', 'Total_Meter_Value')
    search_fields = ('Equipment__Equipment_Number',)
    list_filter = ('Date', 'Equipment')