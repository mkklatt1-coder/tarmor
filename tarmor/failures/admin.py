from django.contrib import admin
from .models import System, Component, FailureType, Action

@admin.register(System)
class System(admin.ModelAdmin):
    list_display = ('combined_sys_key', 'asset_key', 'system_name', 'system_key')
    list_filter = ('combined_sys_key', 'asset_key', 'system_name', 'system_key')
    search_fields = ('system_name', 'system_key')
    
    fieldsets = (
        ('Identity', {'fields': ('asset_key', 'system_name', 'system_key', 'combined_sys_key')}),
    )

@admin.register(Component)
class Component(admin.ModelAdmin):
    list_display = ('component_name', 'component_key', 'combined_sys_key', 'combined_comp_key')
    list_filter = ('component_name', 'component_key', 'combined_comp_key')
    search_fields = ('component_name', 'combined_comp_key')
    
    fieldsets = (
        ('Identity', {'fields': ('component_name', 'component_key', 'combined_sys_key', 'combined_comp_key')}),
    )
    
@admin.register(FailureType)
class FailureType(admin.ModelAdmin):
    list_display = ('failure_mode', 'failure_code')
    list_filter = ('failure_mode', 'failure_code')
    search_fields = ('failure_mode', 'failure_code')
    
    fieldsets = (
        ('Identity', {'fields': ('failure_mode', 'failure_code')}),
    )
    
@admin.register(Action)
class Action(admin.ModelAdmin):
    list_display = ('action_name', 'action_key')
    list_filter = ('action_name', 'action_key')
    search_fields = ('action_name', 'action_key')
    
    fieldsets = (
        ('Identity', {'fields': ('action_name', 'action_key')}),
    )