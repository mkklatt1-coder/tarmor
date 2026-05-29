from django.contrib import admin
from .models import Timesheet

@admin.register(Timesheet)
class TimesheetAdmin(admin.ModelAdmin):
    list_display = ('work_order', 'technician', 'start_date', 'finish_date', 'total_time', 'time_type')
    list_filter = ('work_order', 'technician', 'start_date')
    search_fields = ('work_order__name', 'technician__name')