from django.contrib import admin
from .models import (
    MOC, MOCPro, MOCCon, MOCAttachment, MOCConsiderations, 
    MOCEffValPoint, Safety, MOCQuestion, MOCQuestionResponse, 
    EffValRule, EffValPointRange
)

# --- Inlines for the MOC Page ---

class MOCProInline(admin.TabularInline):
    model = MOCPro
    extra = 0

class MOCConInline(admin.TabularInline):
    model = MOCCon
    extra = 0

class MOCAttachmentInline(admin.TabularInline):
    model = MOCAttachment
    extra = 0

class MOCConsiderationsInline(admin.StackedInline):
    model = MOCConsiderations
    can_delete = False  # Since it's a OneToOneField

class SafetyInline(admin.StackedInline):
    model = Safety
    can_delete = False

# --- Model Admin Classes ---

@admin.register(MOC)
class MOCAdmin(admin.ModelAdmin):
    list_display = ('moc_number', 'title', 'status', 'date_created', 'date_completed')
    list_filter = ('status', 'date_created')
    search_fields = ('moc_number', 'title', 'define_change')
    readonly_fields = ('date_created',)
    
    # This brings everything together on one screen
    inlines = [
        MOCConsiderationsInline,
        SafetyInline,
        MOCProInline,
        MOCConInline,
        MOCAttachmentInline
    ]

@admin.register(MOCQuestion)
class MOCQuestionAdmin(admin.ModelAdmin):
    list_display = ('section', 'text', 'order')
    list_editable = ('order',)
    list_filter = ('section',)

@admin.register(MOCQuestionResponse)
class MOCQuestionResponseAdmin(admin.ModelAdmin):
    list_display = ('moc', 'question', 'dropdown_answer', 'complete')
    list_filter = ('complete', 'question__section')
    search_fields = ('moc__moc_number', 'question__text')

class EffValPointRangeInline(admin.TabularInline):
    model = EffValPointRange
    extra = 1

@admin.register(EffValRule)
class EffValRuleAdmin(admin.ModelAdmin):
    list_display = ('label', 'category', 'source_field', 'weight')
    list_filter = ('category',)
    inlines = [EffValPointRangeInline]

# Simple registration for leftovers
admin.site.register(MOCEffValPoint)
