from django import forms
from django.forms import inlineformset_factory
from .models import (
    QualityMaintenance,
    QualityMaintenanceStep
)

class QualityMaintenanceCreateForm(forms.ModelForm):
    class Meta:
        model = QualityMaintenance
        fields = [
            'qm_number',
            'equipment',
            'description',
            'qm_type',
            'step_type',
            'start_date',
            'meter_start',
            'meter_type',
            'single_interval_value',
            'calendar_unit',
            'est_work_hours',
            'single_interval_checklist',
            'work_order_lead_days',
            'active',
        ]
        widgets = {
            'single_interval_checklist': forms.ClearableFileInput(attrs={
                'class': 'input',
                'accept': '.pdf'
            }),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'input'}),
            'qm_number': forms.TextInput(attrs={'class': 'locked', 'readonly': 'readonly'}),
            'equipment': forms.Select(attrs={'class': 'input'}),
            'description': forms.TextInput(attrs={'class': 'input'}),
            'qm_type': forms.Select(attrs={'class': 'input'}),
            'step_type': forms.Select(attrs={'class': 'input'}),
            'meter_start': forms.NumberInput(attrs={'class': 'input'}),
            'meter_type': forms.Select(attrs={'class': 'input'}),
            'single_interval_value': forms.NumberInput(attrs={'class': 'input'}),
            'calendar_unit': forms.Select(attrs={'class': 'input'}),
            'work_order_lead_days': forms.NumberInput(attrs={'class': 'input'}),
            'est_work_hours': forms.NumberInput(attrs={'class': 'input'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['qm_number'].required = False
        self.fields['qm_number'].disabled = True
        if not self.instance.pk:
            self.initial['qm_number'] = QualityMaintenance.get_next_number()
    def clean(self):
        cleaned = super().clean()
        qm_type = cleaned.get('qm_type')
        step_type = cleaned.get('step_type')
        if qm_type == 'CALENDAR':
            cleaned['meter_start'] = None
            cleaned['meter_type'] = None
            if step_type == 'SINGLE':
                if cleaned.get('single_interval_value') is None:
                    self.add_error('single_interval_value', 'Required for calendar single-step QM.')
                if not cleaned.get('calendar_unit'):
                    self.add_error('calendar_unit', 'Required for calendar single-step QM.')
        elif qm_type == 'METER':
            cleaned['calendar_unit'] = None
            if cleaned.get('meter_start') is None:
                self.add_error('meter_start', 'Required for meter QM.')
            if not cleaned.get('meter_type'):
                self.add_error('meter_type', 'Required for meter QM.')
            if step_type == 'SINGLE' and cleaned.get('single_interval_value') is None:
                self.add_error('single_interval_value', 'Required for meter single-step QM.')
        return super().clean()
    def save(self, commit=True):
        return super().save(commit=commit)
    
class QualityMaintenanceEditForm(forms.ModelForm):
    class Meta:
        model = QualityMaintenance
        fields = [
            'qm_number',
            'equipment',
            'description',
            'qm_type',
            'step_type',
            'start_date',
            'meter_start',
            'meter_type',
            'single_interval_value',
            'calendar_unit',
            'single_interval_checklist',
            'est_work_hours',
            'work_order_lead_days',
            'active',
        ]
        widgets = {
            'single_interval_checklist': forms.ClearableFileInput(attrs={
                'class': 'input',
                'accept': '.pdf'
            }),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'input'}),
            'qm_number': forms.TextInput(attrs={'class': 'locked', 'readonly': 'readonly'}),
            'equipment': forms.Select(attrs={'class': 'input'}),
            'description': forms.TextInput(attrs={'class': 'input'}),
            'qm_type': forms.Select(attrs={'class': 'input'}),
            'step_type': forms.Select(attrs={'class': 'input'}),
            'meter_start': forms.NumberInput(attrs={'class': 'input'}),
            'meter_type': forms.Select(attrs={'class': 'input'}),
            'est_work_hours': forms.NumberInput(attrs={'class': 'input'}),
            'single_interval_value': forms.NumberInput(attrs={'class': 'input'}),
            'calendar_unit': forms.Select(attrs={'class': 'input'}),
            'work_order_lead_days': forms.NumberInput(attrs={'class': 'input'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['qm_number'].disabled = True
    def clean(self):
        cleaned = super().clean()
        qm_type = cleaned.get('qm_type')
        step_type = cleaned.get('step_type')
        if qm_type == 'CALENDAR':
            cleaned['meter_start'] = None
            cleaned['meter_type'] = None
            if step_type == 'SINGLE':
                if cleaned.get('single_interval_value') is None:
                    self.add_error('single_interval_value', 'Required for calendar single-step QM.')
                if not cleaned.get('calendar_unit'):
                    self.add_error('calendar_unit', 'Required for calendar single-step QM.')
        elif qm_type == 'METER':
            cleaned['calendar_unit'] = None
            if cleaned.get('meter_start') is None:
                self.add_error('meter_start', 'Required for meter QM.')
            if not cleaned.get('meter_type'):
                self.add_error('meter_type', 'Required for meter QM.')
            if step_type == 'SINGLE' and cleaned.get('single_interval_value') is None:
                self.add_error('single_interval_value', 'Required for meter single-step QM.')
        return cleaned
    
class QualityMaintenanceStepForm(forms.ModelForm):
    class Meta:
        
        model = QualityMaintenanceStep
        fields = ['step_order', 'interval_value', 'interval_unit', 'step_label', 'est_work_hours', 'step_checklist']
        widgets = {
            'step_checklist': forms.ClearableFileInput(attrs={
                'class': 'input',
                'accept': '.pdf'  # Restricts the file browser to PDFs
            }),
            'step_order': forms.NumberInput(attrs={'class': 'input'}),
            'interval_value': forms.NumberInput(attrs={'class': 'input'}),
            'interval_unit': forms.Select(attrs={'class': 'input'}),
            'step_label': forms.TextInput(attrs={'class': 'input'}),
            'est_work_hours': forms.NumberInput(attrs={'class': 'input'}),
        }
        
QualityMaintenanceStepFormSet = inlineformset_factory(
    QualityMaintenance,
    QualityMaintenanceStep,
    form=QualityMaintenanceStepForm,
    extra=0,
    can_delete=True
)

class QualityMaintenanceSearchForm(forms.Form):
    qm_number = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'input'}))
    equipment_number = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'input'}))
    description = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'input'}))
    qm_type = forms.ChoiceField(
        required=False,
        choices=[('', '---------')] + QualityMaintenance.QM_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'input'})
    )
    step_type = forms.ChoiceField(
        required=False,
        choices=[('', '---------')] + QualityMaintenance.STEP_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'input'})
    )
    active = forms.NullBooleanField(required=False, widget=forms.Select(attrs={'class': 'input'}))
    
class QualityMaintenanceEditLookupForm(forms.Form):
    qm_number = forms.ModelChoiceField(
        queryset=QualityMaintenance.objects.all().order_by('qm_number'),
        empty_label='Select QM',
        label='QM Number',
        widget=forms.Select(attrs={'class': 'input'})
    )