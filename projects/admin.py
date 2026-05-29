from django.contrib import admin
from .models import (
    Project,
    ProjectStep,
    ProjectDelay,
    ProjectAttachment,
    ProjectBudget,
    ProjectNote,
    ProjectLesson,
    ProjectFinancial,
    ProjectTasks,
    CompanyBudget,
)
class ProjectStepInline(admin.TabularInline):
    model = ProjectStep
    extra = 1
    fields = (
        "step_number",
        "description",
        "time_to_implement",
        "uom",
        "start_date",
        "status",
    )
class ProjectDelayInline(admin.TabularInline):
    model = ProjectDelay
    extra = 1
    fields = (
        "step",
        "delay_type",
        "cause",
        "time_requirement",
        "uom",
    )
class ProjectAttachmentInline(admin.TabularInline):
    model = ProjectAttachment
    extra = 1
    fields = (
        "name",
        "file",
    )
class ProjectBudgetInline(admin.TabularInline):
    model = ProjectBudget
    extra = 1
    fields = (
        "year",
        "allocated_budget",
        "yearly_spend",
        "yearly_remaining",
    )
    readonly_fields = (
        "yearly_spend",
        "yearly_remaining",
    )
class ProjectNoteInline(admin.TabularInline):
    model = ProjectNote
    extra = 1
    fields = (
        "step",
        "date",
        "step_note",
        "action",
        "due_date",
        "progress",
        "completed_date",
        "complete",
    )
class ProjectLessonInline(admin.TabularInline):
    model = ProjectLesson
    extra = 1
    fields = (
        "step",
        "date",
        "failure",
        "action",
        "lesson",
        "progress",
        "completed_date",
        "complete",
    )
class ProjectTasksInline(admin.TabularInline):
    model = ProjectTasks
    extra = 1
    fields = (
        "step",
        "date",
        "tasks",
        "assignee",
        "due_date",
        "progress",
        "completed_date",
        "complete",
    )
class ProjectFinancialInline(admin.StackedInline):
    model = ProjectFinancial
    extra = 0
    fields = (
        "year",
        "jan_p",
        "feb_p",
        "mar_p",
        "apr_p",
        "may_p",
        "jun_p",
        "jul_p",
        "aug_p",
        "sep_p",
        "oct_p",
        "nov_p",
        "dec_p",
        "cost_carryover",
        "cash_carryover",
        "planned_total",
        "cost_total",
        "cash_total",
    )
    readonly_fields = (
        "planned_total",
        "cost_total",
        "cash_total",
    )
@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        "project_number",
        "description",
        "moc_number",
        "assigned_to",
        "start_year",
        "status",
        "budget",
        "spend",
        "remaining",
        "completion_percentage",
        "ve_ratio",
    )
    list_filter = (
        "status",
        "start_year",
        "assigned_to",
    )
    search_fields = (
        "project_number",
        "description",
        "moc_number",
        "assigned_to",
        "scope",
        "justification",
    )
    readonly_fields = (
        "project_number",
        "budget",
        "spend",
        "remaining",
        "completion_percentage",
        "ve_ratio",
    )
    fieldsets = (
        (
            "Project Information",
            {
                "fields": (
                    "project_number",
                    "description",
                    "moc_number",
                    "assigned_to",
                    "start_year",
                    "execution_time",
                    "uom",
                    "status",
                )
            },
        ),
        (
            "Financial Summary",
            {
                "fields": (
                    "budget",
                    "spend",
                    "remaining",
                    "ve_ratio",
                )
            },
        ),
        (
            "Progress",
            {
                "fields": (
                    "completion_percentage",
                )
            },
        ),
        (
            "Details",
            {
                "fields": (
                    "scope",
                    "justification",
                )
            },
        ),
    )
    inlines = [
        ProjectStepInline,
        ProjectDelayInline,
        ProjectBudgetInline,
        ProjectFinancialInline,
        ProjectTasksInline,
        ProjectNoteInline,
        ProjectLessonInline,
        ProjectAttachmentInline,
    ]
    ordering = (
        "-project_number",
    )
@admin.register(ProjectStep)
class ProjectStepAdmin(admin.ModelAdmin):
    list_display = (
        "project",
        "step_number",
        "description",
        "time_to_implement",
        "uom",
        "start_date",
        "status",
        "end_date",
        "delay_days",
        "final_date",
    )
    list_filter = (
        "status",
        "uom",
        "start_date",
        "project",
    )
    search_fields = (
        "project__project_number",
        "project__description",
        "description",
        "status",
    )
    readonly_fields = (
        "end_date",
        "delay_days",
        "final_date",
    )
    ordering = (
        "project",
        "step_number",
    )
    @admin.display(description="End Date")
    def end_date(self, obj):
        return obj.get_end_date()
    @admin.display(description="Delay Days")
    def delay_days(self, obj):
        return obj.get_delay_days()
    @admin.display(description="Final Date")
    def final_date(self, obj):
        return obj.get_final_date()
@admin.register(ProjectDelay)
class ProjectDelayAdmin(admin.ModelAdmin):
    list_display = (
        "project",
        "step",
        "delay_type",
        "cause",
        "time_requirement",
        "uom",
    )
    list_filter = (
        "delay_type",
        "cause",
        "uom",
        "project",
    )
    search_fields = (
        "project__project_number",
        "project__description",
        "step__description",
        "delay_type",
        "cause",
    )
    ordering = (
        "project",
        "step",
    )
@admin.register(ProjectAttachment)
class ProjectAttachmentAdmin(admin.ModelAdmin):
    list_display = (
        "project",
        "name",
        "file",
    )
    search_fields = (
        "project__project_number",
        "project__description",
        "name",
        "file",
    )
    list_filter = (
        "project",
    )
@admin.register(ProjectBudget)
class ProjectBudgetAdmin(admin.ModelAdmin):
    list_display = (
        "project",
        "year",
        "allocated_budget",
        "yearly_spend",
        "yearly_remaining",
    )
    list_filter = (
        "year",
        "project",
    )
    search_fields = (
        "project__project_number",
        "project__description",
    )
    readonly_fields = (
        "yearly_spend",
        "yearly_remaining",
    )
    ordering = (
        "project",
        "year",
    )
@admin.register(ProjectNote)
class ProjectNoteAdmin(admin.ModelAdmin):
    list_display = (
        "project",
        "step",
        "date",
        "step_note",
        "due_date",
        "completed_date",
        "complete",
    )
    list_filter = (
        "complete",
        "date",
        "due_date",
        "completed_date",
        "project",
    )
    search_fields = (
        "project__project_number",
        "project__description",
        "step__description",
        "step_note",
        "action",
        "progress",
    )
    date_hierarchy = "date"
    ordering = (
        "-date",
        "-id",
    )
@admin.register(ProjectLesson)
class ProjectLessonAdmin(admin.ModelAdmin):
    list_display = (
        "project",
        "step",
        "date",
        "failure",
        "lesson",
        "completed_date",
        "complete",
    )
    list_filter = (
        "complete",
        "date",
        "completed_date",
        "project",
    )
    search_fields = (
        "project__project_number",
        "project__description",
        "step__description",
        "failure",
        "action",
        "lesson",
        "progress",
    )
    date_hierarchy = "date"
    ordering = (
        "-date",
        "-id",
    )
@admin.register(ProjectFinancial)
class ProjectFinancialAdmin(admin.ModelAdmin):
    list_display = (
        "project",
        "year",
        "planned_total",
        "cost_total",
        "cash_total",
        "cost_carryover",
        "cash_carryover",
    )
    list_filter = (
        "year",
        "project",
    )
    search_fields = (
        "project__project_number",
        "project__description",
    )
    readonly_fields = (
        "planned_total",
        "jan_cost",
        "feb_cost",
        "mar_cost",
        "apr_cost",
        "may_cost",
        "jun_cost",
        "jul_cost",
        "aug_cost",
        "sep_cost",
        "oct_cost",
        "nov_cost",
        "dec_cost",
        "cost_total",
        "jan_cash",
        "feb_cash",
        "mar_cash",
        "apr_cash",
        "may_cash",
        "jun_cash",
        "jul_cash",
        "aug_cash",
        "sep_cash",
        "oct_cash",
        "nov_cash",
        "dec_cash",
        "cash_total",
    )
    fieldsets = (
        (
            "Project",
            {
                "fields": (
                    "project",
                    "year",
                )
            },
        ),
        (
            "Planned Monthly Spend",
            {
                "fields": (
                    "jan_p",
                    "feb_p",
                    "mar_p",
                    "apr_p",
                    "may_p",
                    "jun_p",
                    "jul_p",
                    "aug_p",
                    "sep_p",
                    "oct_p",
                    "nov_p",
                    "dec_p",
                    "planned_total",
                )
            },
        ),
        (
            "Monthly Cost",
            {
                "fields": (
                    "jan_cost",
                    "feb_cost",
                    "mar_cost",
                    "apr_cost",
                    "may_cost",
                    "jun_cost",
                    "jul_cost",
                    "aug_cost",
                    "sep_cost",
                    "oct_cost",
                    "nov_cost",
                    "dec_cost",
                    "cost_total",
                )
            },
        ),
        (
            "Monthly Cash",
            {
                "fields": (
                    "jan_cash",
                    "feb_cash",
                    "mar_cash",
                    "apr_cash",
                    "may_cash",
                    "jun_cash",
                    "jul_cash",
                    "aug_cash",
                    "sep_cash",
                    "oct_cash",
                    "nov_cash",
                    "dec_cash",
                    "cash_total",
                )
            },
        ),
        (
            "Carryover",
            {
                "fields": (
                    "cost_carryover",
                    "cash_carryover",
                )
            },
        ),
    )
    ordering = (
        "project",
        "year",
    )
@admin.register(ProjectTasks)
class ProjectTasksAdmin(admin.ModelAdmin):
    list_display = (
        "project",
        "step",
        "date",
        "tasks",
        "assignee",
        "due_date",
        "completed_date",
        "complete",
    )
    list_filter = (
        "complete",
        "assignee",
        "date",
        "due_date",
        "completed_date",
        "project",
    )
    search_fields = (
        "project__project_number",
        "project__description",
        "step__description",
        "tasks",
        "assignee",
        "progress",
    )
    date_hierarchy = "date"
    ordering = (
        "-date",
        "-id",
    )
@admin.register(CompanyBudget)
class CompanyBudgetAdmin(admin.ModelAdmin):
    list_display = (
        "year",
        "amount",
    )
    list_filter = (
        "year",
    )
    search_fields = (
        "year",
    )
    ordering = (
        "-year",
    )