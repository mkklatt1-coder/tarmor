from django.contrib import admin
from django.utils import timezone
from .models import WeekSetup, WorkWeek, Schedule, ScheduleSnapshot, DailyCrewCapacity

class WorkWeekInline(admin.TabularInline):
    model = WorkWeek
    extra = 0
    readonly_fields = ('week_number', 'start_date', 'end_date')
    can_delete = False

@admin.register(WeekSetup)
class WeekSetupAdmin(admin.ModelAdmin):
    list_display = ('week1_start_date', 'start_day', 'active', 'created_at')
    list_filter = ('active', 'start_day')
    inlines = [WorkWeekInline]
    actions = ['set_active']

    @admin.action(description="Make selected setup active")
    def set_active(self, request, queryset):
        if queryset.count() > 1:
            self.message_user(request, "Please select only one setup to activate.", level='error')
            return
        setup = queryset.first()
        setup.active = True
        setup.save()
        self.message_user(request, f"Setup for {setup.week1_start_date} is now active.")

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('week', 'responsible_garage', 'locked', 'locked_at', 'last_saved')
    list_filter = ('locked', 'responsible_garage', 'week__start_date')
    search_fields = ('responsible_garage__name', 'week__week_number')
    actions = ['lock_schedules']

    @admin.action(description="Lock selected schedules")
    def lock_schedules(self, request, queryset):
        for schedule in queryset:
            schedule.lock()
        self.message_user(request, f"{queryset.count()} schedules have been locked.")

@admin.register(DailyCrewCapacity)
class DailyCrewCapacityAdmin(admin.ModelAdmin):
    list_display = ('date', 'crew', 'workweek', 'available_hours', 'assigned_hours', 'utilization')
    list_filter = ('crew', 'date', 'workweek')
    readonly_fields = ('assigned_hours',)

    def utilization(self, obj):
        if obj.available_hours > 0:
            percent = (obj.assigned_hours / obj.available_hours) * 100
            return f"{percent:.1f}%"
        return "0%"
    utilization.short_description = "Util %"

@admin.register(ScheduleSnapshot)
class ScheduleSnapshotAdmin(admin.ModelAdmin):
    list_display = ('work_order', 'schedule', 'job_status_snapshot', 'plan_start_snapshot')
    list_filter = ('job_status_snapshot', 'plan_start_snapshot')
    readonly_fields = [f.name for f in ScheduleSnapshot._meta.fields] 