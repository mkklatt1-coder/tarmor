from django import forms
from .models import (ShortTermCM, MagPlug, FilterRating, ValveSet, ValveSetReading, CylinderTemp, TireInformation, TireFailure, TireChange, TireChangeInfo, RimInspection,
                     CylinderTempReading, BucketLip, LipMeasurement, BoxLiner, LinerMeasurement, CycleTime, CycleTimeMeasurement, TireInspection, TireInspectionReading)
from django.forms import modelformset_factory, inlineformset_factory, BaseInlineFormSet
from equipment.models import Equipment, Meter
from work_orders.models import WorkOrder
from purchasing.models import Purchase

class ActionItemForm(forms.ModelForm):
    class Meta:
        model = ShortTermCM
        fields = '__all__'
        widgets = {
            'equipment_desc': forms.TextInput(),
            'troubleshoot_desc': forms.TextInput(),
            'repair_desc': forms.TextInput(),
            'date': forms.DateInput(attrs={'type': 'date'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'completed_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            existing_classes = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f'{existing_classes} input'.strip()

        readonly_fields = ['equipment_desc', 'troubleshoot_desc', 'repair_desc']

        for field_name in readonly_fields:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs['readonly'] = True
                self.fields['completed_date'].required = False
                current_classes = self.fields[field_name].widget.attrs.get('class', '')
                self.fields[field_name].widget.attrs['class'] = f'{current_classes} readonly-field'.strip()

class MagPlugForm(forms.ModelForm):
    class Meta:
        model = MagPlug
        fields = '__all__'
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if 'equipment' in self.fields:
            self.fields['equipment'].label_from_instance = lambda obj: f"{obj.Equipment_Number} - {obj.Equipment_Description}"
            
        if 'work_order' in self.fields:
            self.fields['work_order'].label_from_instance = lambda obj: f"{obj.work_order} - {obj.troubleshoot_description}"
            
            if self.instance and self.instance.work_order_id:
                self.initial['work_order'] = self.instance.work_order_id
        
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'input'})
            
        if 'equipment' in self.fields:
            self.fields['equipment'].widget.attrs.update({'class': 'input eq-select'})
        if 'meter' in self.fields:
            self.fields['meter'].widget.attrs.update({'class': 'input meter-select'})

MagPlugFormSet = modelformset_factory(MagPlug, form=MagPlugForm, extra=1)


class MagPlugSearchForm(forms.Form):
    date = forms.DateField(
        required=False, 
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'input'})
    )
    equipment = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'input', 'list': 'equipment-list', 'placeholder': 'Type to filter...'})
    )
    work_order = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'input', 'list': 'workorder-list', 'placeholder': 'Type to filter...'})
    )
    compartment = forms.ChoiceField(
        choices=[('', 'All Compartments')] + list(MagPlug._meta.get_field('compartment').choices),
        required=False,
        widget=forms.Select(attrs={'class': 'input'})
    )

class FilterRatingForm(forms.ModelForm):
    class Meta:
        model = FilterRating
        fields = '__all__'
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if 'equipment' in self.fields:
            self.fields['equipment'].label_from_instance = lambda obj: f"{obj.Equipment_Number} - {obj.Equipment_Description}"
            
        if 'work_order' in self.fields:
            self.fields['work_order'].label_from_instance = lambda obj: f"{obj.work_order} - {obj.troubleshoot_description}"
            
            if self.instance and self.instance.work_order_id:
                self.initial['work_order'] = self.instance.work_order_id
        
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'input'})
            
        if 'equipment' in self.fields:
            self.fields['equipment'].widget.attrs.update({'class': 'input eq-select'})
        if 'meter' in self.fields:
            self.fields['meter'].widget.attrs.update({'class': 'input meter-select'})

FilterRatingFormSet = modelformset_factory(FilterRating, form=FilterRatingForm, extra=1)

class FilterRatingSearchForm(forms.Form):
    date = forms.DateField(
        required=False, 
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'input'})
    )
    equipment = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'input', 'list': 'equipment-list', 'placeholder': 'Type to filter...'})
    )
    work_order = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'input', 'list': 'workorder-list', 'placeholder': 'Type to filter...'})
    )
    compartment = forms.ChoiceField(
        choices=[('', 'All Compartments')] + list(FilterRating._meta.get_field('compartment').choices),
        required=False,
        widget=forms.Select(attrs={'class': 'input'})
    )

class ValveSetForm(forms.ModelForm):
    class Meta:
        model = ValveSet
        fields = [
            'date',
            'equipment',
            'work_order',
            'meter',
            'meter_reading',
            'comments',
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'comments': forms.TextInput(attrs={'size': 40}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'input'})


class ValveSetReadingForm(forms.ModelForm):
    class Meta:
        model = ValveSetReading
        fields = [
            'cylinder_number',
            'int_exh',
            'valve_number',
            'valve_setting',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'input'})


ValveSetReadingFormSet = inlineformset_factory(
    ValveSet,
    ValveSetReading,
    form=ValveSetReadingForm,
    extra=1,
    can_delete=True
)

class CylinderTempForm(forms.ModelForm):
    class Meta:
        model = CylinderTemp
        fields = [
            'date',
            'equipment',
            'work_order',
            'meter',
            'meter_reading',
            'comments',
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'comments': forms.TextInput(attrs={'size': 40}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'input'})


class CylinderTempReadingForm(forms.ModelForm):
    class Meta:
        model = CylinderTempReading
        fields = [
            'cylinder_number',
            'temp_reading',
            'uom',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'input'})


CylinderTempReadingFormSet = inlineformset_factory(
    CylinderTemp,
    CylinderTempReading,
    form=CylinderTempReadingForm,
    extra=1,
    can_delete=True
)

class BucketLipForm(forms.ModelForm):
    class Meta:
        model = BucketLip
        fields = [
            'date',
            'equipment',
            'work_order',
            'meter',
            'meter_reading',
            'comments',
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'comments': forms.TextInput(attrs={'size': 40}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'input'})


class LipMeasurementForm(forms.ModelForm):
    class Meta:
        model = LipMeasurement
        fields = [
            'left_side',
            'right_side',
            'centre',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'input'})


LipMeasurementFormSet = inlineformset_factory(
    BucketLip,
    LipMeasurement,
    form=LipMeasurementForm,
    extra=1,
    can_delete=True
)

class BoxLinerForm(forms.ModelForm):
    class Meta:
        model = BoxLiner
        fields = [
            'date',
            'equipment',
            'work_order',
            'meter',
            'meter_reading',
            'comments',
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'comments': forms.TextInput(attrs={'size': 40}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'input'})


class LinerMeasurementForm(forms.ModelForm):
    class Meta:
        model = LinerMeasurement
        fields = [
            'position',
            'pos_reading',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'input'})

LinerMeasurementFormSet = inlineformset_factory(
    BoxLiner,
    LinerMeasurement,
    form=LinerMeasurementForm,
    extra=1,
    can_delete=True
)

class CycleTimeForm(forms.ModelForm):
    class Meta:
        model = CycleTime
        fields = [
            'date',
            'equipment',
            'work_order',
            'meter',
            'meter_reading',
            'comments',
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'comments': forms.TextInput(attrs={'size': 40}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'input'})


class CycleTimeMeasurementForm(forms.ModelForm):
    class Meta:
        model = CycleTimeMeasurement
        fields = [
            'system',
            'position',
            'time',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'input'})

CycleTimeMeasurementFormSet = inlineformset_factory(
    CycleTime,
    CycleTimeMeasurement,
    form=CycleTimeMeasurementForm,
    extra=1,
    can_delete=True
)

class TireInformationForm(forms.ModelForm):
    class Meta:
        model = TireInformation
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'input'})

        if 'asset_type' in self.data:
            try:
                asset_type_id = int(self.data.get('asset_type'))
                from equipment.models import EQ_Type
                self.fields['equipment_type'].queryset = EQ_Type.objects.filter(Asset_Type_id=asset_type_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.asset_type:
            self.fields['equipment_type'].queryset = self.instance.asset_type.equipment_types.all()

TireInformationFormSet = modelformset_factory(TireInformation, form=TireInformationForm, extra=1)

class TireFailureTypeForm(forms.ModelForm):
    class Meta:
        model = TireFailure
        fields = ['failure_mode']
        widgets = {
            'failure_mode': forms.TextInput(attrs={'placeholder': 'Enter failure type...'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['failure_mode'].widget.attrs.update({'class': 'input'})


class TireChangeForm(forms.ModelForm):
    class Meta:
        model = TireChange
        fields = [
            'date',
            'equipment',
            'work_order',
            'meter',
            'meter_reading',
            'comments',
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'comments': forms.TextInput(attrs={'size': 40}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'input'})

class TireChangeInfoForm(forms.ModelForm):
    class Meta:
        model = TireChangeInfo
        fields = [
            'tire_id_off',
            'tire_id_on',
            'position',
            'tread_depth_off',
            'tread_depth_on',
            'rim_id_off',
            'rim_id_on',
            'reason_for_failure',
            'inflation_pressure',
            'scrapped',
            'recapped',
            'scrap_reason',
            'purchase_order',
            'tire_cost',
            
        ]

    def __init__(self, *args, **kwargs):
        wo_number_str = kwargs.pop('work_order_str', None)
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'input'})

        self.fields['tire_cost'].disabled = True
        self.fields['tire_cost'].required = False
        self.fields['tire_cost'].widget.attrs.update({'class': 'locked'})


        if wo_number_str:
            self.fields['purchase_order'].queryset = Purchase.objects.filter(
                wo_cc=str(wo_number_str).strip()
            )
        else:
            self.fields['purchase_order'].queryset = Purchase.objects.none()

class BaseTireChangeInfoFormSet(BaseInlineFormSet):
    def get_form_kwargs(self, index):
        kwargs = super().get_form_kwargs(index)
        if self.instance and hasattr(self.instance, 'work_order') and self.instance.work_order:
            kwargs['work_order_str'] = self.instance.work_order.work_order
        return kwargs

TireChangeInfoFormSet = inlineformset_factory(
    TireChange,
    TireChangeInfo,
    form=TireChangeInfoForm,
    formset=BaseTireChangeInfoFormSet,
    extra=0,
    can_delete=True
)

class TireInspectionForm(forms.ModelForm):
    class Meta:
        model = TireInspection
        fields = [
            'date',
            'equipment',
            'work_order',
            'meter',
            'meter_reading',
            'comments',
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'comments': forms.TextInput(attrs={'size': 40}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'input'})

class TireInspectionReadingForm(forms.ModelForm):
    class Meta:
        model = TireInspectionReading
        fields = [
            'tire_id',
            'position',
            'tread_depth',
            'inflation_pressure',
            'tire_diameter',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'input'})

TireInspectionReadingFormSet = inlineformset_factory(
    TireInspection,
    TireInspectionReading,
    form=TireInspectionReadingForm,
    extra=0,
    can_delete=True,
)

class RimInspectionForm(forms.ModelForm):
    class Meta:
        model = RimInspection
        fields = [
            'date_tested',
            'rim_id',
            'pass_fail',
            'failure_reason',
            'last_test_date',
            'number_of_tests',
            'next_test_date',
        ]
        widgets = {
            'date_tested': forms.DateInput(attrs={'type': 'date'}),
            'last_test_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'input'})

RimInspectionFormSet = modelformset_factory(RimInspection, form=RimInspectionForm, extra=1)