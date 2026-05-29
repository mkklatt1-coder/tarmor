from django.contrib import admin
from .models import (
    ShortTermCM,
    MagPlug,
    FilterRating,
    ValveSet,
    ValveSetReading,
    CylinderTemp,
    CylinderTempReading,
    BucketLip,
    LipMeasurement,
    BoxLiner,
    LinerMeasurement,
    CycleTime,
    CycleTimeMeasurement,
    TireInformation,
    TireChange,
    TireChangeInfo,
    TireFailure,
    TireInspection,
    TireInspectionReading,
    RimInspection,
)

@admin.register(ShortTermCM)
class ShortTermCMAdmin(admin.ModelAdmin):
    list_display = (
        "date",
        "equipment",
        "equipment_desc",
        "work_order",
        "problem",
        "corrective_action",
        "due_date",
        "progress",
        "complete",
        "completed_date",
    )
    list_filter = (
        "progress",
        "complete",
        "date",
        "due_date",
        "completed_date",
    )
    search_fields = (
        "equipment__unit",
        "equipment_desc",
        "work_order__work_order_number",
        "problem",
        "corrective_action",
        "troubleshoot_desc",
        "repair_desc",
    )
    date_hierarchy = "date"
    ordering = ("-date", "-id")

@admin.register(MagPlug)
class MagPlugAdmin(admin.ModelAdmin):
    list_display = (
        "date",
        "equipment",
        "work_order",
        "meter",
        "meter_reading",
        "compartment",
        "plug_rating",
        "comments",
    )
    list_filter = (
        "date",
        "compartment",
        "plug_rating",
    )
    search_fields = (
        "equipment__unit",
        "work_order__work_order_number",
        "comments",
    )
    date_hierarchy = "date"
    ordering = ("-date", "-id")

@admin.register(FilterRating)
class FilterRatingAdmin(admin.ModelAdmin):
    list_display = (
        "date",
        "equipment",
        "work_order",
        "meter",
        "meter_reading",
        "compartment",
        "filter_rating",
        "comments",
    )
    list_filter = (
        "date",
        "compartment",
        "filter_rating",
    )
    search_fields = (
        "equipment__unit",
        "work_order__work_order_number",
        "comments",
    )
    date_hierarchy = "date"
    ordering = ("-date", "-id")

class ValveSetReadingInline(admin.TabularInline):
    model = ValveSetReading
    extra = 1
    fields = (
        "cylinder_number",
        "int_exh",
        "valve_number",
        "valve_setting",
    )

@admin.register(ValveSet)
class ValveSetAdmin(admin.ModelAdmin):
    list_display = (
        "date",
        "equipment",
        "work_order",
        "meter",
        "meter_reading",
        "comments",
    )
    list_filter = (
        "date",
        "equipment",
    )
    search_fields = (
        "equipment__unit",
        "work_order__work_order_number",
        "comments",
    )
    date_hierarchy = "date"
    ordering = ("-date", "-id")
    inlines = [ValveSetReadingInline]

@admin.register(ValveSetReading)
class ValveSetReadingAdmin(admin.ModelAdmin):
    list_display = (
        "valve_set",
        "cylinder_number",
        "int_exh",
        "valve_number",
        "valve_setting",
    )
    list_filter = (
        "cylinder_number",
        "int_exh",
        "valve_number",
    )
    search_fields = (
        "valve_set__equipment__unit",
        "valve_set__work_order__work_order_number",
    )

class CylinderTempReadingInline(admin.TabularInline):
    model = CylinderTempReading
    extra = 1
    fields = (
        "cylinder_number",
        "temp_reading",
        "uom",
    )

@admin.register(CylinderTemp)
class CylinderTempAdmin(admin.ModelAdmin):
    list_display = (
        "date",
        "equipment",
        "work_order",
        "meter",
        "meter_reading",
        "comments",
    )
    list_filter = (
        "date",
        "equipment",
    )
    search_fields = (
        "equipment__unit",
        "work_order__work_order_number",
        "comments",
    )
    date_hierarchy = "date"
    ordering = ("-date", "-id")
    inlines = [CylinderTempReadingInline]

@admin.register(CylinderTempReading)
class CylinderTempReadingAdmin(admin.ModelAdmin):
    list_display = (
        "cylinder_temp",
        "cylinder_number",
        "temp_reading",
        "uom",
    )
    list_filter = (
        "cylinder_number",
        "uom",
    )
    search_fields = (
        "cylinder_temp__equipment__unit",
        "cylinder_temp__work_order__work_order_number",
    )

class LipMeasurementInline(admin.TabularInline):
    model = LipMeasurement
    extra = 1
    fields = (
        "left_side",
        "right_side",
        "centre",
    )

@admin.register(BucketLip)
class BucketLipAdmin(admin.ModelAdmin):
    list_display = (
        "date",
        "equipment",
        "work_order",
        "meter",
        "meter_reading",
        "comments",
    )
    list_filter = (
        "date",
        "equipment",
    )
    search_fields = (
        "equipment__unit",
        "work_order__work_order_number",
        "comments",
    )
    date_hierarchy = "date"
    ordering = ("-date", "-id")
    inlines = [LipMeasurementInline]

@admin.register(LipMeasurement)
class LipMeasurementAdmin(admin.ModelAdmin):
    list_display = (
        "bucket_lip",
        "left_side",
        "right_side",
        "centre",
    )
    search_fields = (
        "bucket_lip__equipment__unit",
        "bucket_lip__work_order__work_order_number",
    )

class LinerMeasurementInline(admin.TabularInline):
    model = LinerMeasurement
    extra = 1
    fields = (
        "position",
        "pos_reading",
    )

@admin.register(BoxLiner)
class BoxLinerAdmin(admin.ModelAdmin):
    list_display = (
        "date",
        "equipment",
        "work_order",
        "meter",
        "meter_reading",
        "comments",
    )
    list_filter = (
        "date",
        "equipment",
    )
    search_fields = (
        "equipment__unit",
        "work_order__work_order_number",
        "comments",
    )
    date_hierarchy = "date"
    ordering = ("-date", "-id")
    inlines = [LinerMeasurementInline]

@admin.register(LinerMeasurement)
class LinerMeasurementAdmin(admin.ModelAdmin):
    list_display = (
        "box_liner",
        "position",
        "pos_reading",
    )
    list_filter = (
        "position",
    )
    search_fields = (
        "box_liner__equipment__unit",
        "box_liner__work_order__work_order_number",
    )

class CycleTimeMeasurementInline(admin.TabularInline):
    model = CycleTimeMeasurement
    extra = 1
    fields = (
        "system",
        "position",
        "time",
    )

@admin.register(CycleTime)
class CycleTimeAdmin(admin.ModelAdmin):
    list_display = (
        "date",
        "equipment",
        "work_order",
        "meter",
        "meter_reading",
        "comments",
    )
    list_filter = (
        "date",
        "equipment",
    )
    search_fields = (
        "equipment__unit",
        "work_order__work_order_number",
        "comments",
    )
    date_hierarchy = "date"
    ordering = ("-date", "-id")
    inlines = [CycleTimeMeasurementInline]

@admin.register(CycleTimeMeasurement)
class CycleTimeMeasurementAdmin(admin.ModelAdmin):
    list_display = (
        "cycle_time",
        "system",
        "position",
        "time",
    )
    list_filter = (
        "system",
        "position",
    )
    search_fields = (
        "cycle_time__equipment__unit",
        "cycle_time__work_order__work_order_number",
    )

@admin.register(TireInformation)
class TireInformationAdmin(admin.ModelAdmin):
    list_display = (
        "asset_type",
        "equipment_type",
        "make",
        "model",
        "tire_size",
        "tire_face",
        "tread_depth_new",
        "inflation_pressure",
        "tire_cost",
    )
    list_filter = (
        "asset_type",
        "equipment_type",
        "tire_face",
        "make",
    )
    search_fields = (
        "make",
        "model",
        "tire_size",
        "asset_type__asset_type",
        "equipment_type__equipment_type",
    )

class TireChangeInfoInline(admin.TabularInline):
    model = TireChangeInfo
    extra = 1
    fields = (
        "position",
        "tire_id_off",
        "tire_id_on",
        "tread_depth_off",
        "tread_depth_on",
        "rim_id_off",
        "rim_id_on",
        "purchase_order",
        "tire_cost",
        "reason_for_failure",
        "inflation_pressure",
        "scrapped",
        "recapped",
        "scrap_reason",
    )

@admin.register(TireChange)
class TireChangeAdmin(admin.ModelAdmin):
    list_display = (
        "date",
        "equipment",
        "work_order",
        "meter",
        "meter_reading",
        "comments",
    )
    list_filter = (
        "date",
        "equipment",
    )
    search_fields = (
        "equipment__unit",
        "work_order__work_order_number",
        "comments",
    )
    date_hierarchy = "date"
    ordering = ("-date", "-id")
    inlines = [TireChangeInfoInline]

@admin.register(TireChangeInfo)
class TireChangeInfoAdmin(admin.ModelAdmin):
    list_display = (
        "tire_change",
        "position",
        "tire_id_off",
        "tire_id_on",
        "tread_depth_off",
        "tread_depth_on",
        "rim_id_off",
        "rim_id_on",
        "purchase_order",
        "tire_cost",
        "reason_for_failure",
        "inflation_pressure",
        "scrapped",
        "recapped",
        "scrap_reason",
    )
    list_filter = (
        "position",
        "scrapped",
        "recapped",
        "reason_for_failure",
        "scrap_reason",
    )
    search_fields = (
        "tire_change__equipment__unit",
        "tire_change__work_order__work_order_number",
        "tire_id_off",
        "tire_id_on",
        "rim_id_off",
        "rim_id_on",
    )

@admin.register(TireFailure)
class TireFailureAdmin(admin.ModelAdmin):
    list_display = (
        "failure_mode",
    )
    search_fields = (
        "failure_mode",
    )
    ordering = (
        "failure_mode",
    )

class TireInspectionReadingInline(admin.TabularInline):
    model = TireInspectionReading
    extra = 1
    fields = (
        "position",
        "tire_id",
        "tread_depth",
        "inflation_pressure",
        "tire_diameter",
    )

@admin.register(TireInspection)
class TireInspectionAdmin(admin.ModelAdmin):
    list_display = (
        "date",
        "equipment",
        "work_order",
        "meter",
        "meter_reading",
        "comments",
    )
    list_filter = (
        "date",
        "equipment",
    )
    search_fields = (
        "equipment__unit",
        "work_order__work_order_number",
        "comments",
    )
    date_hierarchy = "date"
    ordering = ("-date", "-id")
    inlines = [TireInspectionReadingInline]

@admin.register(TireInspectionReading)
class TireInspectionReadingAdmin(admin.ModelAdmin):
    list_display = (
        "tire_inspection",
        "position",
        "tire_id",
        "tread_depth",
        "inflation_pressure",
        "tire_diameter",
    )
    list_filter = (
        "position",
    )
    search_fields = (
        "tire_inspection__equipment__unit",
        "tire_inspection__work_order__work_order_number",
        "tire_id",
    )
    
@admin.register(RimInspection)
class RimInspectionAdmin(admin.ModelAdmin):
    list_display = (
        "date_tested",
        "rim_id",
        "pass_fail",
        "failure_reason",
        "last_test_date",
        "number_of_tests",
        "next_test_date",
    )
    list_filter = (
        "date_tested",
        "pass_fail",
        "failure_reason",
    )
    search_fields = (
        "rim_id",
        "failure_reason",
    )
    readonly_fields = (
        "next_test_date",
    )
    date_hierarchy = "date_tested"
    ordering = ("-date_tested", "-id")
