from django import forms
from django.forms import inlineformset_factory
from .models import QualityMaintenanceDocument, QualityMaintenanceDocumentStep, QualityMaintenancePlan
from equipment.models import Equipment, Meter

class QualityMaintenanceCreateForm(forms.ModelForm):
    class Meta:
        model = QualityMaintenanceDocument
        fields = [
            'qm_number', 'description', 'qm_type', 'step_type',
            'single_interval_value', 'calendar_unit', 'est_work_hours',
            'single_interval_checklist', 'work_order_lead_days', 'active', 'single_interval_parts_list',
        ]
        widgets = {
            'single_interval_checklist': forms.ClearableFileInput(attrs={
                'class': 'input',
                'accept': '.pdf'
            }),
            'single_interval_parts_list': forms.ClearableFileInput(attrs={
                'class': 'input',
                'accept': '.pdf'
            }),
            'qm_number': forms.TextInput(attrs={'class': 'locked', 'readonly': 'readonly'}),
            'description': forms.TextInput(attrs={'class': 'input'}),
            'qm_type': forms.Select(attrs={'class': 'input'}),
            'step_type': forms.Select(attrs={'class': 'input'}),
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
            self.initial['qm_number'] = QualityMaintenanceDocument.get_next_number()

    def clean(self):
        cleaned = super().clean()
        qm_type = cleaned.get('qm_type')
        step_type = cleaned.get('step_type')

        if step_type == 'SINGLE':
            if cleaned.get('single_interval_value') is None:
                self.add_error('single_interval_value', 'Required for single-step QM.')
            
            if qm_type == 'CALENDAR' and not cleaned.get('calendar_unit'):
                self.add_error('calendar_unit', 'Calendar unit is required for single-step Calendar QM.')
            
            if qm_type == 'METER':
                cleaned['calendar_unit'] = None
        
        return cleaned
    
class QualityMaintenanceEditForm(QualityMaintenanceCreateForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['qm_number'].disabled = True

    
class QualityMaintenanceStepForm(forms.ModelForm):
    class Meta:
        
        model = QualityMaintenanceDocumentStep
        fields = ['step_order', 'interval_value', 'interval_unit', 'step_label', 'est_work_hours', 'step_checklist', 'step_parts_list']
        widgets = {
            'step_checklist': forms.ClearableFileInput(attrs={
                'class': 'input',
                'accept': '.pdf'
            }),
            'step_parts_list': forms.ClearableFileInput(attrs={
                'class': 'input',
                'accept': '.pdf'
            }),
            'step_order': forms.NumberInput(attrs={'class': 'input'}),
            'interval_value': forms.NumberInput(attrs={'class': 'input'}),
            'interval_unit': forms.Select(attrs={'class': 'input'}),
            'step_label': forms.TextInput(attrs={'class': 'input'}),
            'est_work_hours': forms.NumberInput(attrs={'class': 'input'}),
        }
        
QualityMaintenanceStepFormSet = inlineformset_factory(
    QualityMaintenanceDocument,
    QualityMaintenanceDocumentStep,

    form=QualityMaintenanceStepForm,
    extra=0,
    can_delete=True
)

class QualityMaintenanceSearchForm(forms.Form):
    qm_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'input', 'list': 'qm-number-list', 'placeholder': 'Search QM...'})
    )
    description = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'input', 'list': 'qm-desc-list', 'placeholder': 'Search Description...'})
    )
    qm_type = forms.ChoiceField(
        required=False,
        choices=[('', '---------')] + QualityMaintenanceDocument.QM_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'input'})
    )
    step_type = forms.ChoiceField(
        required=False,
        choices=[('', '---------')] + QualityMaintenanceDocument.STEP_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'input'})
    )
    active = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All Statuses'),
            ('Yes', 'Yes (Active)'),
            ('No', 'No (Inactive)')
        ],
        widget=forms.Select(attrs={'class': 'input'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            existing = field.widget.attrs.get('class', '')
            if 'input' not in existing.split():
                field.widget.attrs['class'] = f'{existing} input'.strip()
    
class QualityMaintenanceEditLookupForm(forms.Form):
    qm_number = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'input', 
            'list': 'qm-lookup-list', 
            'placeholder': 'Type Number or Description...',
            'autocomplete': 'off'
        })
    )
    
class QualityMaintenancePlanForm(forms.ModelForm):
    document = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'input',
            'list': 'document-suggestions',
            'placeholder': 'Type document or description...',
            'autocomplete': 'off'
        })
    )
    equipment = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'input',
            'list': 'equipment-suggestions',
            'placeholder': 'Type equipment or description...',
            'autocomplete': 'off',
            'hx-get': '/planning/get-linked-meters/',
            'hx-trigger': 'input changed delay:300ms, change',
            'hx-target': '#meter-type-datalist-wrapper',
        })
    )
    meter_type = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'input',
            'list': 'meter-type-suggestions',
            'placeholder': 'Select equipment first...',
            'autocomplete': 'off'
        })
    )

    class Meta:
        model = QualityMaintenancePlan
        fields = ['document', 'equipment', 'active', 'start_date', 'meter_start', 'meter_type']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            existing_classes = field.widget.attrs.get('class', '')
            if 'input' not in existing_classes.split():
                field.widget.attrs['class'] = f'{existing_classes} input'.strip()

        if 'start_date' in self.fields:
            self.fields['start_date'].widget = forms.DateInput(attrs={'type': 'date', 'class': 'input'})

        if self.instance and self.instance.pk:
            if self.instance.document:
                self.initial['document'] = self.instance.document.qm_number
            if self.instance.equipment:
                self.initial['equipment'] = self.instance.equipment.Equipment_Number
            if self.instance.meter_type:
                self.initial['meter_type'] = self.instance.meter_type.meter_type

    def clean_document(self):
        qm_str = self.cleaned_data.get('document')
        doc = QualityMaintenanceDocument.objects.filter(qm_number=qm_str).first()
        if not doc:
            raise forms.ValidationError(f"Quality Maintenance Document '{qm_str}' does not exist.")
        return doc

    def clean_equipment(self):
        eq_str = self.cleaned_data.get('equipment')
        eq = Equipment.objects.filter(Equipment_Number=eq_str).first()
        if not eq:
            raise forms.ValidationError(f"Equipment Unit '{eq_str}' does not exist.")
        return eq

    def clean_meter_type(self):
        mt_str = self.cleaned_data.get('meter_type')
        if not mt_str:
            return None
        mt = Meter.objects.filter(meter_type=mt_str).first()
        if not mt:
            raise forms.ValidationError(f"Meter Type '{mt_str}' does not exist.")
        return mt