from django.contrib import admin
from .models import CostCentre, Facility

@admin.register(CostCentre)
class CostCentreAdmin(admin.ModelAdmin):
    list_display = ("Cost_Centre", "Cost_Centre_Description", "Status")
    
    list_filter = ("Status",)
    
    search_fields = ("Cost_Centre", "Cost_Centre_Description")

@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display = ("Facility_Code", "Facility_Name", "Cost_Centre", "City", "Contact_Name")
    
    list_filter = ("City", "Province_State", "Cost_Centre")
    
    search_fields = ("Facility_Code", "Facility_Name", "Contact_Name", "City")
    
    fieldsets = (
        ("Basic Information", {
            "fields": ("Facility_Code", "Facility_Name", "Cost_Centre", "Status")
        }),
        ("Location Details", {
            "fields": ("Street_Address", "City", "Province_State", "Country", "Postal_Zip_Code")
        }),
        ("Contact & Support", {
            "fields": ("Contact_Name", "Contact_Phone_Number", "Email_Address", "Additional_Information")
        }),
    )