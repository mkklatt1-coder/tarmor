from django.contrib import admin
from .models import Equipment, EQ_Type, Meter, Component, ComponentType, AssetType, ComponentHistory
from import_export.admin import ImportExportModelAdmin
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget

class EqAdmin(admin.ModelAdmin):
    list_display = ('Equipment_Number', 'Asset_Type', 'Equipment_Type', 'Equipment_Status')
    readonly_fields = ('id',)

@admin.register(ComponentType)
class ComponentTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_code')

@admin.register(AssetType)
class AssetTypeAdmin(admin.ModelAdmin):
    list_display = ['name']

@admin.register(Equipment)
class EquipmentAdmin(ImportExportModelAdmin):
    list_display = ['Equipment_Number', 'Equipment_Description']
    search_fields = ['Equipment_Number', 'Equipment_Description']

@admin.register(Meter)
class MeterAdmin(admin.ModelAdmin):
    list_display = ['meter_type', 'equipment']
    search_fields = ['meter_type']

@admin.register(EQ_Type)
class EQTypeAdmin(admin.ModelAdmin):
    list_display = ['Equipment_Type', 'Asset_Type', 'Prefix']

@admin.register(ComponentHistory)
class ComponentHistoryAdmin(admin.ModelAdmin):
    list_display = (
        'Change_Date',
        'Equipment',
        'Component',
        'Change_Type',
        'Work_Order_Number',
        'New_Serial'
    )
    list_filter = ('Change_Type', 'Change_Date', 'Meter_Description')
    search_fields = (
        'Equipment__Equipment_Number',
        'Component__Component_Number',
        'Work_Order_Number',
        'New_Serial',
        'Old_Serial'
    )
    fieldsets = (
        ('Event Details', {
            'fields': ('Equipment', 'Component', 'Work_Order_Number', 'Change_Date', 'Change_Type')
        }),
        ('Meter Information', {
            'fields': ('Meter_Description', 'Meter_Reading')
        }),
        ('Technical Details (New Component)', {
            'fields': ('New_Make', 'New_Model', 'New_Serial', 'Old_Serial', 'New_PO', 'New_Lifespan')
        }),
        ('Warranty Information', {
            'fields': ('New_Wty_Dur', 'New_Wty_UoM', 'New_Wty_Start', 'New_Wty_End')
        }),
        ('Notes', {
            'fields': ('Additional_Information', 'Date_Recorded')
        }),
    )

class ComponentResource(resources.ModelResource):
    Equipment_id = fields.Field(
        column_name='Equipment_id',
        attribute='Equipment',
        widget=ForeignKeyWidget(Equipment, 'id')
    )
    Component_Type_id = fields.Field(
        column_name='Component_Type_id',
        attribute='Component_Type',
        widget=ForeignKeyWidget(ComponentType, 'id')
    )
    class Meta:
        model = Component
        fields = (
            'id', 'Component_Number', 'Equipment_id', 'Component_Type_id', 'Make', 'Model',
            'Serial_Number', 'Expected_Lifespan', 'UoM', 'PO_Number', 'Warranty_Duration',
            'Wty_UoM', 'Warranty_Start_Date', 'Warranty_End_Date', 'Additional_Information',
            'Installation_Date', 'Removal_Date', 'Status', 'Component_Description'
        )
        import_id_fields = ('id',)
        
@admin.register(Component)
class ComponentAdmin(ImportExportModelAdmin):
    resource_class = ComponentResource