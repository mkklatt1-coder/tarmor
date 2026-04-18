from django import forms
from equipment.models import Equipment
from .models import WorkOrder

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
                
class WorkOrderEditForm(forms.ModelForm):
    class Meta:
        model = WorkOrder
        fields = [
            'attached_checklist',
            'equipment',
            'barcode_image',
            'work_type',
            'priority',
            'machine_oos',
            'hours',
            'meter',
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