from django.contrib import admin
from .models import Employee, EmployeeCertification, ShiftPattern, Crew, CrewShiftRotation
from django import forms

class EmployeeCertificationInline(admin.TabularInline):
    model = EmployeeCertification
    extra = 1  # Provides one empty slot for new certifications
    fields = ('Certification', 'Institution', 'Date_Cert', 'Renewable', 'Renewal_Cost')

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('First_Name', 'Last_Name', 'Position', 'Status', 'Compensation', 'Comp_UoM', 'Email')
    list_filter = ('Status', 'Comp_UoM', 'Prov_State', 'Country')
    search_fields = ('First_Name', 'Last_Name', 'Email', 'Position')
    
    # Groups fields into sections for a cleaner edit form
    fieldsets = (
        ('Basic Information', {
            'fields': (('First_Name', 'Middle_Name', 'Last_Name'), ('Status', 'Position'))
        }),
        ('Compensation & Employment', {
            'fields': (('Compensation', 'Comp_UoM'), ('Start_Date', 'Last_Date'), ('crew'))
        }),
        ('Contact Details', {
            'fields': ('Phone', 'Email', 'Street_Address', 'City', 'Prov_State', 'Country', 'Postal_Zip')
        }),
        ('Emergency Contact', {
            'fields': (('EC_First_Name', 'EC_Middle_Name', 'EC_Last_Name'), ('EC_Phone', 'EC_Email'))
        }),
        ('Notes', {
            'fields': ('Additional_Information',)
        }),
    )

    inlines = [EmployeeCertificationInline]

@admin.register(EmployeeCertification)
class EmployeeCertificationAdmin(admin.ModelAdmin):
    list_display = ('Employee', 'Certification', 'Institution', 'Date_Cert', 'Renewable')
    list_filter = ('Renewable', 'Date_Cert')
    search_fields = ('Employee__First_Name', 'Employee__Last_Name', 'Certification')

@admin.register(ShiftPattern)
class ShiftPatternAdmin(admin.ModelAdmin):
    list_display = ('name', 'pattern_sequence', 'is_rotating')
    search_fields = ('name', 'pattern_sequence')

@admin.register(Crew)
class CrewAdmin(admin.ModelAdmin):
    list_display = ('full_shift_id', 'location_code', 'shift_letter', 'pattern', 'start_date', 'province')
    list_filter = ('province', 'pattern', 'location_code')
    search_fields = ('location_code', 'shift_letter')
    
    fieldsets = (
        ('Identity', {'fields': ('location_code', 'shift_letter', 'province')}),
        ('Schedule Logic', {'fields': ('pattern', 'start_date')}),
    )
        
@admin.register(CrewShiftRotation)
class CrewShiftRotationAdmin(admin.ModelAdmin):
    
    list_display = ('Shift_ID', 'Location', 'Coverage_Type', 'Calendar_Month', 'Start_Date', 'batch_id', 'created_at')
    list_filter = ('Coverage_Type', 'Calendar_Month', 'province', 'created_at') 
    search_fields = ('Shift_ID', 'Location__Facility_Code', 'batch_id') 
    
    readonly_fields = ('Shift_ID', 'batch_id', 'created_at')
    
    fieldsets = (
        ('Deployment', {'fields': ('Shift_ID', 'Location', 'province', 'batch_id')}),
        ('Timing', {'fields': ('Calendar_Month', 'Start_Date', 'created_at')}),
        ('Logic', {'fields': ('Coverage_Type', 'pattern')}),
    )