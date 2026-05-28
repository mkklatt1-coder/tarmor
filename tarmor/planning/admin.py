from django.contrib import admin
from .models import (
    QualityMaintenanceDocument, 
    QualityMaintenanceDocumentStep, 
    QualityMaintenancePlan,
    QualityMaintenanceInstance
)

class QualityMaintenanceDocumentStepInline(admin.TabularInline):
    model = QualityMaintenanceDocumentStep
    extra = 1
    fields = ('step_order', 'interval_value', 'interval_unit', 'step_label', 'est_work_hours')

@admin.register(QualityMaintenanceDocument)
class QualityMaintenanceDocumentAdmin(admin.ModelAdmin):
    list_display = ('qm_number', 'description', 'qm_type', 'step_type', 'active')
    list_filter = ('qm_type', 'step_type', 'active')
    search_fields = ('qm_number', 'description')
    inlines = [QualityMaintenanceDocumentStepInline]
    
    fieldsets = (
        ('Header Information', {
            'fields': ('qm_number', 'description', 'active')
        }),
        ('Configuration', {
            'fields': ('qm_type', 'step_type', 'work_order_lead_days')
        }),
        ('Single Step Details', {
            'description': 'Only used if Step Type is set to SINGLE',
            'fields': (
                'single_interval_value', 'calendar_unit', 'est_work_hours', 
                'single_interval_checklist', 'single_interval_parts_list'
            )
        }),
    )

@admin.register(QualityMaintenancePlan)
class QualityMaintenancePlanAdmin(admin.ModelAdmin):
    list_display = (
        'equipment', 
        'document', 
        'current_meter_display', 
        'avg_usage_display', 
        'active'
    )
    list_filter = ('active', 'document__qm_type')
    search_fields = ('equipment__equipment_number', 'document__qm_number')
    autocomplete_fields = ['equipment', 'document', 'meter_type']

    def current_meter_display(self, obj):
        return f"{obj.get_current_meter():,.0f}"
    current_meter_display.short_description = "Current Meter"

    def avg_usage_display(self, obj):
        usage = obj.get_average_daily_usage()
        return f"{usage:.2f}/day" if usage else "N/A"
    avg_usage_display.short_description = "Avg Daily Usage"


@admin.register(QualityMaintenanceInstance)
class QualityMaintenanceInstanceAdmin(admin.ModelAdmin):
    list_display = (
        'plan', 
        'step_display', 
        'colored_status', 
        'due_date', 
        'due_meter', 
        'work_order_link'
    )
    list_filter = ('status', 'due_date', 'plan__document__qm_type')
    search_fields = ('plan__equipment__equipment_number', 'work_order__work_order_number')
    
    readonly_fields = ('created_at', 'plan', 'step', 'due_date', 'due_meter')

    def step_display(self, obj):
        if obj.step:
            return f"Step {obj.step.step_order}: {obj.step.step_label}"
        return "Single Step"
    step_display.short_description = "Maintenance Step"

    def colored_status(self, obj):
        colors = {
            'COMPLETE': 'green',
            'TRIGGERED': 'orange',
            'DUE': 'red',
            'FORECAST': 'blue',
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<b style="color: {};">{}</b>',
            color,
            obj.get_status_display()
        )
    colored_status.short_description = "Status"

    def work_order_link(self, obj):
        if obj.work_order:
            # Assumes your work_order model has an admin page
            return format_html(
                '<a href="/admin/work_orders/workorder/{}/change/">{}</a>',
                obj.work_order.id,
                obj.work_order
            )
        return "No Work Order"
    work_order_link.short_description = "Linked WO"

# Add this to QualityMaintenancePlanAdmin to see instances as a list
class QualityMaintenanceInstanceInline(admin.TabularInline):
    model = QualityMaintenanceInstance
    extra = 0
    readonly_fields = ('due_date', 'due_meter', 'work_order', 'status', 'completed_date')
    can_delete = False