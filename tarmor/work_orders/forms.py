from django import forms
from equipment.models import Equipment
from .models import WorkOrder, WorkOrderAttachment

class DateTimeLocalInput(forms.DateTimeInput):
    input_type = 'datetime-local'
    def __init__(self, **kwargs):
        kwargs.setdefault('attrs', {}).update({'step': 'any'})
        super().__init__(**kwargs)
    
class WorkOrderAddForm(forms.ModelForm):
    class Meta:
        model = WorkOrder
        fields = [
            'equipment',
            'barcode_image',
            'work_type',
            'priority',
            'machine_oos',
            'hours',
            'meter',
            'project',
            'job_status',
            'date_created',
            'troubleshoot_description',
            'ts_extended_description',
            'equipment_location',
            'ts_service_report',
            'est_work_hours',
            'repair_description',
            'repair_extended_description',
            'job_instructions',
            'fc_system',
            'fc_component',
            'fc_failure_mode',
            'fc_action',
            'repair_service_report',
            'plan_start_date',
            'safety_instructions',
            'spec_requirements',
            'legislative',
            'license_req',
            'tools_req',
            'conf_space',
            'jha',
            'hot_work',
            'parts_wty',
            'work_wty',
        ]
        widgets = {
            'date_created': DateTimeLocalInput(),
            'plan_start_date': DateTimeLocalInput(),
            'ts_extended_description': forms.Textarea(attrs={'class': 'input', 'rows': 10, 'style': 'width: 100%'}),
            'ts_service_report': forms.Textarea(attrs={'class': 'input', 'rows': 10, 'style': 'width: 100%'}),
            'repair_extended_description': forms.Textarea(attrs={'class': 'input', 'rows': 10, 'style': 'width: 100%'}),
            'job_instructions': forms.Textarea(attrs={'class': 'input', 'rows': 10, 'style': 'width: 100%'}),
            'repair_service_report': forms.Textarea(attrs={'class': 'input', 'rows': 10, 'style': 'width: 90%'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        posted_equipment_id = None
        if self.data.get('equipment'):
            posted_equipment_id = self.data.get('equipment')
        elif self.instance and self.instance.pk and self.instance.equipment_id:
            posted_equipment_id = self.instance.equipment_id
        if posted_equipment_id:
            self.fields['equipment'].queryset = Equipment.objects.filter(pk=posted_equipment_id)
        else:
            self.fields['equipment'].queryset = Equipment.objects.none()
        for field_name in ['date_created', 'plan_start_date']:
            self.fields[field_name].input_formats = [
                '%Y-%m-%dT%H:%M',
                '%Y-%m-%d %H:%M',
                '%m/%d/%Y %H:%M',
                '%m/%d/%Y %I:%M %p',
            ]
        for name, field in self.fields.items():
            field.widget.attrs.update({'class': 'input'})

        if self.initial.get('project') or (self.instance and self.instance.project):
            self.fields['project'].widget.attrs['class'] = 'locked'

    def clean(self):
        cleaned_data = super().clean()
        
        if cleaned_data is not None:
            potential_problem_fields = [
                'project', 'equipment', 'fc_system', 
                'fc_component', 'fc_failure_mode', 'fc_action'
            ]
            
            for field in potential_problem_fields:
                value = cleaned_data.get(field)
                
                if isinstance(value, str) and value.strip() in ('None', 'null', ''):
                    cleaned_data[field] = None
                    
        return cleaned_data

class WorkOrderEditForm(forms.ModelForm):
    class Meta:
        model = WorkOrder
        fields = [
            'attached_checklist',
            'attached_parts_list',
            'equipment',
            'barcode_image',
            'work_type',
            'priority',
            'machine_oos',
            'hours',
            'meter',
            'project',
            'job_status',
            'date_created',
            'date_closed',
            'troubleshoot_description',
            'ts_extended_description',
            'equipment_location',
            'est_work_hours',
            'ts_service_report',
            'repair_description',
            'repair_extended_description',
            'job_instructions',
            'fc_system',
            'fc_component',
            'fc_failure_mode',
            'fc_action',
            'repair_service_report',
            'plan_start_date',
            'safety_instructions',
            'spec_requirements',
            'legislative',
            'license_req',
            'tools_req',
            'conf_space',
            'jha',
            'hot_work',
            'parts_wty',
            'work_wty',
        ]
        widgets = {
            'date_created': DateTimeLocalInput(),
            'date_closed': DateTimeLocalInput(),
            'plan_start_date': DateTimeLocalInput(),
            'attached_checklist': forms.FileInput(attrs={'id': 'id_attached_checklist', 'class': 'input', 'accept': '.pdf'}),
            'attached_parts_list': forms.FileInput(attrs={'id': 'id_attached_parts_list', 'class': 'input', 'accept': '.pdf'}),
            'ts_extended_description': forms.Textarea(attrs={'class': 'input', 'rows': 10, 'style': 'width: 100%'}),
            'ts_service_report': forms.Textarea(attrs={'class': 'input', 'rows': 10, 'style': 'width: 100%'}),
            'repair_extended_description': forms.Textarea(attrs={'class': 'input', 'rows': 10, 'style': 'width: 100%'}),
            'job_instructions': forms.Textarea(attrs={'class': 'input', 'rows': 10, 'style': 'width: 100%'}),
            'repair_service_report': forms.Textarea(attrs={'class': 'input', 'rows': 10, 'style': 'width: 100%'}),
            'safety_instructions': forms.Textarea(attrs={'class': 'input', 'rows': 10, 'style': 'width: 90%'}),
            'spec_requirements': forms.Textarea(attrs={'class': 'input', 'rows': 10, 'style': 'width: 90%'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        posted_equipment_id = None
        if self.data.get('equipment'):
            posted_equipment_id = self.data.get('equipment')
        elif self.instance and self.instance.pk and self.instance.equipment_id:
            posted_equipment_id = self.instance.equipment_id
        if posted_equipment_id:
            self.fields['equipment'].queryset = Equipment.objects.filter(pk=posted_equipment_id)
        else:
            self.fields['equipment'].queryset = Equipment.objects.none()
        for field_name in ['date_created', 'date_closed', 'plan_start_date']:
            self.fields[field_name].input_formats = [
                '%Y-%m-%dT%H:%M',
                '%Y-%m-%d %H:%M',
                '%m/%d/%Y %H:%M',
                '%m/%d/%Y %I:%M %p',
            ]
        for name, field in self.fields.items():
            field.widget.attrs.update({'class': 'input'})
        
        if self.initial.get('project') or (self.instance and self.instance.project):
            self.fields['project'].widget.attrs['class'] = 'locked'

class AttachmentsForm(forms.ModelForm):
    class Meta:
        model = WorkOrderAttachment
        fields = ['description', 'file']

    widgets = {
        'description': forms.TextInput(attrs={
                'class': 'input', 
                'placeholder': 'Enter name...',
                'style': 'flex-grow: 1;'
            }),
        "file": forms.FileInput(attrs={"class": "input"}),
    }

AttachmentsFormSet = forms.modelformset_factory(
    WorkOrderAttachment, 
    form=AttachmentsForm, 
    extra=0,
    can_delete=True
)