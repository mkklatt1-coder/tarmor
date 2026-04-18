from django import forms
from .models import System, Component, FailureType, Action
from django.forms import modelformset_factory, BaseModelFormSet
from django.core.exceptions import ValidationError


class SystemForm(forms.ModelForm):
    class Meta:
        model = System
        fields = [
            'asset_key',
            'system_name',
            'system_key',
        ]
        
    def clean_asset_key(self):
        value = self.cleaned_data["asset_key"].strip().upper()

        if value not in ['F', 'M']:
            raise forms.ValidationError("asset_key must be F or M")
        elif len(value) != 1:
            raise forms.ValidationError("Asset key must be exactly 1 character.")
        return value
        
    def clean_system_key(self):
        value = self.cleaned_data["system_key"].strip().upper()
        if len(value) != 3:
            raise forms.ValidationError("System key must be exactly 3 characters.")
        return value
    
    def clean(self):
        cleaned_data = super().clean()
        asset_key = cleaned_data.get("asset_key")
        system_key = cleaned_data.get("system_key")
        
        if asset_key and system_key:
            combined_sys_key = f"{asset_key}{system_key}"
            cleaned_data["combined_sys_key"] = combined_sys_key
            
            qs = System.objects.filter(combined_sys_key=combined_sys_key)
            
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
                
            if qs.exists():
                raise forms.ValidationError(
                    f"System code {combined_sys_key} already exists."
                )
                
        return cleaned_data
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for _, field in self.fields.items():
            field.widget.attrs.update({'class': 'input'})
            
class BaseSystemFormSet(BaseModelFormSet):
    def clean(self):
        super().clean()
        seen = set()
        for form in self.forms:
            if not hasattr(form, "cleaned_data"):
                continue
            if not form.cleaned_data:
                continue
            if form.errors:
                continue
            if form.cleaned_data.get("DELETE"):
                continue
            asset_key = form.cleaned_data.get("asset_key")
            system_key = form.cleaned_data.get("system_key")
            if not asset_key or not system_key:
                continue
            combined_sys_key = f"{asset_key}{system_key}"
            if combined_sys_key in seen:
                raise ValidationError(
                    f"Duplicate entry in this submission: {combined_sys_key}"
                )
            seen.add(combined_sys_key)
            
SystemFormSet = modelformset_factory(
    System,
    form=SystemForm,
    formset=BaseSystemFormSet,
    extra=1,
    can_delete=False
)

class SystemEditForm(SystemForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if self.instance and self.instance.pk:
            self.fields['asset_key'].widget.attrs['readonly'] = True
            self.fields['system_key'].widget.attrs['readonly'] = True
            self.fields['asset_key'].widget.attrs.update({
                'class': 'locked','style': 'pointer-events: none'
            })
            self.fields['system_key'].widget.attrs.update({
                'class': 'locked','style': 'pointer-events: none'
            })

SystemEditFormSet = modelformset_factory(
    System,
    form=SystemEditForm,
    formset=BaseSystemFormSet,
    extra=0,
    can_delete=False
)

class CsvImportForm(forms.Form):
    csv_file = forms.FileField(label="Select CSV file")
    
class ComponentEditForm(forms.ModelForm):
    class Meta:
        model = Component
        fields = ['component_name', 'component_key', 'combined_sys_key', 'combined_comp_key']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['combined_comp_key'].required = False
        
        if self.instance and self.instance.pk:
            self.fields['combined_sys_key'].initial = self.instance.combined_sys_key.combined_sys_key
            
        self.fields['combined_comp_key'].widget.attrs.update({'readonly': 'readonly', 'class': 'locked'})
        self.fields['combined_sys_key'].widget.attrs.update({'readonly': 'readonly', 'class': 'locked'})
        self.fields['component_key'].widget.attrs.update({'class': 'input'})
        self.fields['component_name'].widget.attrs.update({'class': 'input'})

class FailureTypeForm(forms.ModelForm):
    class Meta:
        model = FailureType
        fields = ['failure_mode', 'failure_code']
        
    def clean_failure_code(self):
        value = self.cleaned_data.get("failure_code","").strip().upper()
        if len(value) != 3:
            raise forms.ValidationError("Failure code must be exactly 3 characters.")
        return value
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.update({'class': 'input'})
            
class FailureTypeEditForm(forms.ModelForm):
    class Meta:
        model = FailureType
        fields = ['failure_mode', 'failure_code']
        
    def clean_failure_code(self):
        value = self.cleaned_data.get("failure_code", "").strip().upper()
        if len(value) != 3:
            raise forms.ValidationError("Failure code must be exactly 4 characters.")
        return value
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
                
        if self.instance and self.instance.pk:
            self.fields['failure_mode'].initial = self.instance.failure_mode
            
        self.fields['failure_mode'].widget.attrs.update({'class': 'input'})
        self.fields['failure_code'].widget.attrs.update({'class': 'input'})
        
class ActionForm(forms.ModelForm):
    class Meta:
        model = Action
        fields = ['action_name', 'action_key']
        
    def clean_action_key(self):
        value = self.cleaned_data.get("action_key","").strip().upper()
        if len(value) != 3:
            raise forms.ValidationError("Action code must be exactly 3 characters.")
        return value
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.update({'class': 'input'})
            
class ActionEditForm(forms.ModelForm):
    class Meta:
        model = Action
        fields = ['action_name', 'action_key']
        
    def clean_action_key(self):
        value = self.cleaned_data.get("action_key", "").strip().upper()
        if len(value) != 3:
            raise forms.ValidationError("Action code must be exactly 3 characters.")
        return value
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
                
        if self.instance and self.instance.pk:
            self.fields['action_name'].initial = self.instance.action_name
            
        self.fields['action_name'].widget.attrs.update({'class': 'input'})
        self.fields['action_key'].widget.attrs.update({'class': 'input'})