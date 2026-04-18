from django.forms import ModelForm, inlineformset_factory
from django import forms
from .models import Equipment, EQ_Type, Meter, METER_CHOICES, AssetType, Component, ComponentType, ComponentHistory, ShiftReport, CAB_CHOICES, TIER_CHOICES, BOX_CHOICES
from facilities.models import Facility

# ---------------------------------------
# Meter Form + Formset
# ---------------------------------------
class MeterForm(forms.ModelForm):
    meter_type = forms.ChoiceField(
        choices=METER_CHOICES,
        widget=forms.Select(attrs={'class': 'input'})
    )
    class Meta:
        model = Meter
        fields = ['meter_type']
MeterFormSet = inlineformset_factory(
    Equipment,
    Meter,
    form=MeterForm,
    extra=0,
    can_delete=True
)
# ---------------------------------------
# Equipment Upload Form
# ---------------------------------------
class EqUploadForm(ModelForm):
    ASSET_CHOICES = [
        ('', 'Select Asset Type'),
        ('Surface Fixed', 'Surface Fixed'),
        ('Surface Mobile', 'Surface Mobile'),
        ('Underground Fixed', 'Underground Fixed'),
        ('Underground Mobile', 'Underground Mobile'),
    ]
    EQUIPMENT_STATUS_CHOICES = [
        ('Select', 'Select'),
        ('In Service', 'In Service'),
        ('Out of Service', 'Out of Service'),
        ('Not Commissioned', 'Not Commissioned'),
        ('Decommissioned', 'Decommissioned'),
    ]
    Asset_Type = forms.ChoiceField(
        choices=[], 
        widget=forms.Select(attrs={'class': 'input'}),
        required=True
    )
    
    Equipment_Type = forms.ModelChoiceField(
        queryset=EQ_Type.objects.none(),
        widget=forms.Select(attrs={'class': 'input'}),
        required=True
    )
    
    Equipment_Status = forms.ChoiceField(
        choices=EQUIPMENT_STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'input'}),
        required=True
    )
    
    Cab_Style = forms.ChoiceField(
        choices=CAB_CHOICES,
        widget=forms.Select(attrs={'class': 'input'}),
        required=False
    )
    
    Eng_Tier = forms.ChoiceField(
        choices=TIER_CHOICES,
        widget=forms.Select(attrs={'class': 'input'}),
        required=False
    )
    
    Box_Type = forms.ChoiceField(
        choices=BOX_CHOICES,
        widget=forms.Select(attrs={'class': 'input'}),
        required=False
    )
    
    class Meta:
        model = Equipment
        exclude = ['Asset_Type', 'Equipment_Type']
        widgets = {
            'Equipment_Number': forms.TextInput(attrs={'class': 'locked', 'readonly': 'readonly'}),
            'Equipment_Description': forms.TextInput(attrs={'class': 'input'}),
            'Commissioning_Date': forms.DateInput(attrs={'class': 'input', 'type': 'date'}),
            'Decommissioning_Date': forms.DateInput(attrs={'class': 'input', 'type': 'date'}),
            'Make': forms.TextInput(attrs={'class': 'input'}),
            'Model': forms.TextInput(attrs={'class': 'input'}),
            'Serial_Number': forms.TextInput(attrs={'class': 'input'}),
            'PO_Number': forms.TextInput(attrs={'class': 'input'}),
            'Equipment_Value': forms.NumberInput(attrs={'class': 'input'}),
            'Warranty_Start_Date': forms.DateInput(attrs={'class': 'input', 'type': 'date'}),
            'Warranty_End_Date': forms.DateInput(attrs={'class': 'input', 'type': 'date'}),
            'Engine_HP_Rating': forms.NumberInput(attrs={'class': 'input'}),
            'CANMET_Number': forms.TextInput(attrs={'class': 'input'}),
            'Ventilation_Rating': forms.TextInput(attrs={'class': 'input'}),
            'Garage': forms.Select(attrs={'class': 'input'}),
            'Overhaul_Period': forms.NumberInput(attrs={'class': 'input'}),
            'Overhaul_Value': forms.NumberInput(attrs={'class': 'input'}),
            'End_of_Life': forms.NumberInput(attrs={'class': 'input'}),
            'Additional_Information': forms.Textarea(attrs={'class': 'input', 'rows': 10, 'cols': 160}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
               
        self.fields['Asset_Type'].choices = [('', 'Select Asset Type')] + \
        [(at.name, at.name) for at in AssetType.objects.all()]
        
        asset_val = self.data.get('Asset_Type') or (
            self.instance.Asset_Type.name if self.instance.pk and self.instance.Asset_Type else None
        )
        
        if asset_val:
            queryset = EQ_Type.objects.filter(Asset_Type__name=asset_val)
            self.fields['Equipment_Type'].queryset = queryset
            
        mobile_types = ["Surface Mobile", "Underground Mobile"]
        
        if asset_val not in mobile_types:
            for f in ['Engine_HP_Rating', 'Eng_Tier', 'Cab_Style']:
                self.fields[f].widget = forms.HiddenInput()
                self.fields[f].required = False

        if asset_val != "Underground Mobile":
            for f in ['CANMET_Number', 'Ventilation_Rating']:
                self.fields[f].widget = forms.HiddenInput()
                self.fields[f].required = False

        eq_type_id = self.data.get('Equipment_Type')
        is_haul_truck = False
        if eq_type_id and str(eq_type_id).isdigit():
            try:
                selected_type = EQ_Type.objects.get(id=eq_type_id)
                if "Haul Truck" in selected_type.Equipment_Type:
                    is_haul_truck = True
            except EQ_Type.DoesNotExist:
                pass
        
        if not is_haul_truck:
            self.fields['Box_Type'].widget = forms.HiddenInput()
            self.fields['Box_Type'].required = False

    def clean(self):
        cleaned_data = super().clean()
        eq_type_obj = cleaned_data.get("Equipment_Type")
        
        if eq_type_obj and "Haul Truck" in eq_type_obj.Equipment_Type:
            if not cleaned_data.get("Box_Type"):
                self.add_error('Box_Type', "Box Type is required for Haul Trucks.")
                
        return cleaned_data
                
# ---------------------------------------
# Equipment Edit Form
# ---------------------------------------
class EqEditForm(ModelForm):
    EQUIPMENT_STATUS_CHOICES = [
        ('Select', 'Select'),
        ('In Service', 'In Service'),
        ('Out of Service', 'Out of Service'),
        ('Not Commissioned', 'Not Commissioned'),
        ('Decommissioned', 'Decommissioned'),
    ]
    Equipment_Status = forms.ChoiceField(
        choices=EQUIPMENT_STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'input'})
    )
    class Meta:
        model = Equipment
        fields = '__all__'
        widgets = {
            'Equipment_Number': forms.TextInput(attrs={'class': 'locked', 'readonly': 'readonly'}),
            'Asset_Type': forms.Select(attrs={'class': 'locked'}),
            'Equipment_Type': forms.Select(attrs={'class': 'input'}),
            'Equipment_Description': forms.TextInput(attrs={'class': 'input'}),
            'Commissioning_Date': forms.DateInput(attrs={'class': 'input', 'type': 'date'}),
            'Decommissioning_Date': forms.DateInput(attrs={'class': 'input', 'type': 'date'}),
            'Make': forms.TextInput(attrs={'class': 'input'}),
            'Model': forms.TextInput(attrs={'class': 'input'}),
            'Serial_Number': forms.TextInput(attrs={'class': 'input'}),
            'PO_Number': forms.TextInput(attrs={'class': 'input'}),
            'Equipment_Value': forms.NumberInput(attrs={'class': 'input'}),
            'Warranty_Start_Date': forms.DateInput(attrs={'class': 'input', 'type': 'date'}),
            'Warranty_End_Date': forms.DateInput(attrs={'class': 'input', 'type': 'date'}),
            'Overhaul_Period': forms.NumberInput(attrs={'class': 'input'}),
            'Overhaul_Value': forms.NumberInput(attrs={'class': 'input'}),
            'End_of_Life': forms.NumberInput(attrs={'class': 'input'}),
            'Engine_HP_Rating': forms.NumberInput(attrs={'class': 'input'}),
            'CANMET_Number': forms.TextInput(attrs={'class': 'input'}),
            'Ventilation_Rating': forms.TextInput(attrs={'class': 'input'}),
            'Garage': forms.Select(attrs={'class': 'input'}),
            'Cab_Style': forms.Select(attrs={'class': 'input'}),
            'Eng_Tier': forms.Select(attrs={'class': 'input'}),
            'Box_Type': forms.Select(attrs={'class': 'input'}),
            'Additional_Information': forms.Textarea(attrs={'class': 'input', 'rows': 10, 'cols': 160}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['Asset_Type'].disabled = True
        if self.instance and self.instance.pk:
            self.fields['Equipment_Type'].queryset = EQ_Type.objects.filter(
                Asset_Type=self.instance.Asset_Type
            )
            
# ---------------------------------------
# Component Upload Form
# ---------------------------------------
class CompUploadForm(ModelForm):
    UoM_CHOICES = [
    ('', 'Select'),
    ('Hours', 'Hours'),
    ('Kilometers', 'Kilometers'),
    ('Cycles', 'Cycles'),
    ('Years', 'Years'),
    ]
    
    WTY_UoM_CHOICES = [
    ('', 'Select'),
    ('Hours', 'Hours'),
    ('Kilometers', 'Kilometers'),
    ('Cycles', 'Cycles'),
    ('Years', 'Years'),
    ]
    
    Component_Type = forms.ModelChoiceField(
        queryset=ComponentType.objects.all(),
        empty_label="Select Component Type",
        widget=forms.Select(attrs={'class': 'input', 'id': 'id_Component_Type'})
    )

    UoM = forms.ChoiceField(
        choices=UoM_CHOICES,
        widget=forms.Select(attrs={'class': 'input'})
    )
    
    Wty_UoM = forms.ChoiceField(
        choices=WTY_UoM_CHOICES,
        widget=forms.Select(attrs={'class': 'input', 'id': 'id_Wty_UoM'})
    )

    Equipment_Number = forms.CharField(
        label='Equipment Number',
        widget=forms.TextInput(attrs={'class': 'locked', 'readonly': 'readonly'}),
        required=False
    )
    
    Equipment_Description = forms.CharField(
        label='Equipment Description',
        widget=forms.TextInput(attrs={'class': 'locked', 'readonly': 'readonly'}),
        required=False
    )
    
    Status = forms.ChoiceField(
        choices=Component.STATUS_CHOICES, 
        initial='Active',
        widget=forms.Select(attrs={'class': 'input'})
    )
        
    class Meta:
        model = Component
        fields = '__all__'
        widgets = {
            'Component_Number': forms.TextInput(attrs={'class': 'locked', 'readonly': 'readonly'}),
            'Component_Description': forms.TextInput(attrs={'class': 'locked', 'readonly': 'readonly'}),
            'Installation_Date': forms.DateInput(attrs={'class': 'input', 'type': 'date'}),
            'Removal_Date': forms.DateInput(attrs={'class': 'input', 'type': 'date'}),
            'Make': forms.TextInput(attrs={'class': 'input'}),
            'Model': forms.TextInput(attrs={'class': 'input'}),
            'Serial_Number': forms.TextInput(attrs={'class': 'input'}),
            'Expected_Lifespan': forms.NumberInput(attrs={'class': 'input'}),
            'PO_Number': forms.TextInput(attrs={'class': 'input'}),
            'Warranty_Duration': forms.NumberInput(attrs={'class': 'input'}),
            'Warranty_Start_Date': forms.DateInput(attrs={'class': 'input', 'type': 'date'}),
            'Warranty_End_Date': forms.DateInput(attrs={'class': 'input', 'type': 'date'}),
            'Additional_Information': forms.Textarea(attrs={'class': 'input', 'rows': 10, 'cols': 160}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['Equipment'].widget = forms.HiddenInput()
        
# ---------------------------------------
# Component Change Form
# ---------------------------------------
class CompChangeForm(forms.ModelForm):
    New_UoM_CHOICES = [
    ('', 'Select'),
    ('Hours', 'Hours'),
    ('Kilometers', 'Kilometers'),
    ('Cycles', 'Cycles'),
    ('Years', 'Years'),
    ]
    
    New_WTY_UoM_CHOICES = [
    ('', 'Select'),
    ('Hours', 'Hours'),
    ('Kilometers', 'Kilometers'),
    ('Cycles', 'Cycles'),
    ('Years', 'Years'),
    ]
    
    New_UoM = forms.ChoiceField(
        choices=New_UoM_CHOICES,
        widget=forms.Select(attrs={'class': 'input'})
    )
    
    New_Wty_UoM = forms.ChoiceField(
        choices=New_WTY_UoM_CHOICES,
        widget=forms.Select(attrs={'class': 'input', 'id': 'id_Wty_UoM'})
    )
    
    Equipment = forms.ModelChoiceField(queryset=Equipment.objects.all(), widget=forms.HiddenInput())
    Component = forms.ModelChoiceField(queryset=Component.objects.all(), widget=forms.HiddenInput())
    
    Component_Number = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'locked', 'readonly': 'readonly'}))
    Component_Description = forms.CharField(max_length=200, required=False, widget=forms.TextInput(attrs={'class': 'locked', 'readonly': 'readonly'}))
    
    New_Lifespan = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'input'}))
    New_PO = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'input'}))
    New_Make = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'input'}))
    New_Model = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'input'}))
    New_Serial = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'input'}))
    New_Wty_Dur = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'input'}))
    New_Wty_Start = forms.DateField(widget=forms.DateInput(attrs={'class': 'input', 'type': 'date'}))
    New_Wty_End = forms.DateField(widget=forms.DateInput(attrs={'class': 'input', 'type': 'date'}))

    class Meta:
            model = ComponentHistory 
            fields = [
                'Equipment', 'Component', 'Work_Order_Number', 'Change_Date', 
                'Change_Type', 'Meter_Description', 'Meter_Reading', 
                'New_Serial', 'New_Make', 'New_Model', 'New_PO', 
                'New_Lifespan', 'New_UoM', 'New_Wty_Dur', 'New_Wty_UoM', 
                'New_Wty_Start', 'New_Wty_End', 'Additional_Information'
            ]
        # Only assign the WIDGET here, not the Field type
            widgets = {
                'Work_Order_Number': forms.TextInput(attrs={'class': 'input'}),
                'Meter_Description': forms.Select(attrs={'class': 'input'}),
                'Meter_Reading': forms.NumberInput(attrs={'class': 'input'}),
                'Change_Type': forms.Select(attrs={'class': 'input'}),
                'Change_Date': forms.DateInput(attrs={'type': 'date', 'class': 'input'}),
                'Additional_Information': forms.Textarea(attrs={'class': 'input', 'rows': 3}),
            }
  
            
class ShiftReportForm(forms.ModelForm):
    asset_type= forms.ModelChoiceField(
        queryset=AssetType.objects.all(), 
        required=False, 
        to_field_name="name"
        )
    garage= forms.ModelChoiceField(
        queryset=Facility.objects.all(), 
        required=False, 
        to_field_name="Facility_Name"
        )
    
    class Meta:
        model = ShiftReport
        fields = ['asset_type', 'garage', 'date', 'shift', 'mining_supervisor', 'maint_supervisor']
        widgets = {
            'date': forms.DateInput(attrs={'class': 'input', 'type': 'date'}),
            'shift': forms.Select(attrs={'class': 'input'}),
            'mining_supervisor': forms.TextInput(attrs={'class': 'input'}),
            'maint_supervisor': forms.TextInput(attrs={'class': 'input'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        shift = cleaned_data.get('shift')
        if date and shift:
            qs = ShiftReport.objects.filter(date=date, shift=shift)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(
                    "A shift report already exists for this date and shift."
                )
        return cleaned_data
    