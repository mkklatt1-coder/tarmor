from django.contrib import admin
from .models import StatusChoices, WorkType, WorkOrder

@admin.register(StatusChoices)
class StatusChoicesAdmin(admin.ModelAdmin):
    list_display = ('status_choice',)

@admin.register(WorkType)
class WorkTypeAdmin(admin.ModelAdmin):
    list_display = ('work_type', 'work_description')

@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = ('work_order', 'equipment_number', 'work_type', 'priority', 'job_status', 'date_created')
    list_filter = ('work_type', 'priority', 'job_status', 'date_created')
    search_fields = ('work_order', 'equipment__Equipment_Number', 'troubleshoot_description')
    readonly_fields = ('work_order', 'barcode_image') 

    fieldsets = (
        ('Header Information', {
            'fields': (('work_order', 'barcode_image'), 'equipment', 'job_status', ('date_created', 'date_closed'))
        }),
        ('Job Details', {
            'fields': (('work_type', 'priority', 'machine_oos'), ('hours', 'meter'))
        }),
        ('Troubleshooting', {
            'fields': ('troubleshoot_description', 'ts_extended_description', 'equipment_location', 'ts_service_report')
        }),
        ('Planning', {
            'classes': ('collapse',), 
            'fields': (
                'plan_start_date', 'safety_instructions', 'spec_requirements',
                ('legislative', 'license_req', 'tools_req'),
                ('conf_space', 'jha'),
                ('parts_wty', 'work_wty')
            )
        }),
        ('Repair & Failures', {
            'fields': (
                'repair_description', 'repair_extended_description', 'job_instructions',
                ('fc_system', 'fc_component'),
                ('fc_failure_mode', 'fc_action'),
                'repair_service_report'
            )
        }),
    )

    def barcode_preview(self, obj):
        if obj.barcode_image:
            from django.utils.html import format_html
            return format_html('<img src="{}" style="height:50px;"/>', obj.barcode_image.url)
        return "No Barcode"
    
    barcode_preview.short_description = 'Barcode'
