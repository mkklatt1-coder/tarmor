from django.contrib import admin
from .models import RebuildPlanRow
@admin.register(RebuildPlanRow)
class RebuildPlanRowAdmin(admin.ModelAdmin):
    list_display = (
        "equipment",
        "intervention_type",
        "intervention_cost",
        "calculated_year",
        "modified_year",
        "planned_year",
        "project_number",
        "is_approved",
        "is_complete",
        "iteration_cycle",
    )
    list_filter = (
        "intervention_type",
        "calculated_year",
        "modified_year",
        "is_approved",
        "is_complete",
        "iteration_cycle",
    )
    search_fields = (
        "equipment__Equipment_Number",
        "project_number",
    )
    readonly_fields = (
        "planned_year",
    )
    ordering = (
        "calculated_year",
        "modified_year",
        "equipment",
        "intervention_type",
    )
    list_editable = (
        "modified_year",
        "project_number",
        "is_approved",
        "is_complete",
    )
    list_per_page = 50