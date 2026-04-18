from django import forms
from django.forms import inlineformset_factory
from .models import Employee, EmployeeCertification, CrewShiftRotation, ShiftPattern, PROVINCE_CHOICES
from datetime import date
from facilities.models import Facility

class NewEmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            'First_Name', 'Middle_Name', 'Last_Name', 'Status',
            'Position', 'Compensation', 'Comp_UoM',
            'crew', 'Start_Date', 'Last_Date',
            'Street_Address', 'City', 'Prov_State', 'Country', 'Postal_Zip',
            'Phone', 'Email',
            'EC_First_Name', 'EC_Middle_Name', 'EC_Last_Name',
            'EC_Phone', 'EC_Email',
            'Additional_Information',
        ]
        widgets = {
            'Start_Date': forms.DateInput(attrs={'type': 'date'}),
            'Last_Date': forms.DateInput(attrs={'type': 'date'}),
            'Additional_Information': forms.Textarea(attrs={'rows': 4}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for _, field in self.fields.items():
            field.widget.attrs.update({'class': 'input'})
            
    def clean_Email(self):
        email = self.cleaned_data.get('Email')
        return email or None
    
    def clean_EC_Email(self):
        email = self.cleaned_data.get('EC_Email')
        return email or None
    
class EmployeeCertificationForm(forms.ModelForm):
    class Meta:
        model = EmployeeCertification
        fields = [
            'Certification',
            'Institution',
            'Date_Cert',
            'Renewable',
            'Renewal_Cost',
        ]
        widgets = {
            'Date_Cert': forms.DateInput(attrs={'type': 'date'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for _, field in self.fields.items():
            field.widget.attrs.update({'class': 'input'})
            
CertificationFormSet = inlineformset_factory(
    Employee,
    EmployeeCertification,
    form=EmployeeCertificationForm,
    extra=0,
    can_delete=True
)

class CrewShiftRotationUploadForm(forms.ModelForm):
    class Meta:
        model = CrewShiftRotation
        fields = ["Location", "Coverage_Type", "Calendar_Month", "Start_Date", "province"]
        widgets = {"Start_Date": forms.DateInput(attrs={"type": "date"}), "pattern": forms.HiddenInput(),}
        labels = {
            "Coverage_Type": "Coverage Type",
            "Calendar_Month": "Target Month",
            "province": "Province"
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'pattern' in self.fields:
            self.fields['pattern'].required = False
        for _, field in self.fields.items():
            field.widget.attrs.update({'class': 'input'})
            
class ShiftPatternForm(forms.ModelForm):
    class Meta:
        model = ShiftPattern
        fields = ["name", "pattern_sequence", "is_rotating"]
        labels = {
            "name": "Pattern Name",
            "pattern_sequence": "Rotation Sequence (e.g. 5,5,4,4)",
            "is_rotating": "Rotates Day/Night?"
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for _, field in self.fields.items():
            field.widget.attrs.update({'class': 'input'})

class ReplaceScheduleBatchForm(forms.Form):
    Location = forms.ModelChoiceField(
        queryset=Facility.objects.all(),
        disabled=True
    )
    Coverage_Type = forms.ChoiceField(
        choices=CrewShiftRotation.COVERAGE_TYPE_CHOICES,
        label="Coverage Type"
    )
    Calendar_Month = forms.ChoiceField(
        choices=CrewShiftRotation.CALENDAR_MONTH_CHOICES,
        label="Target Month"
    )
    Start_Date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="New Schedule Start Date"
    )
    pattern = forms.ModelChoiceField(
        queryset=ShiftPattern.objects.all(),
        label="Shift Pattern"
    )
    province = forms.ChoiceField(
        choices=PROVINCE_CHOICES,
        label="Province"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for _, field in self.fields.items():
            field.widget.attrs.update({'class': 'input'})
            
    def clean_Start_Date(self):
        start_date = self.cleaned_data['Start_Date']
        if start_date <= date.today():
            raise forms.ValidationError("Replacement schedule must use a future date.")
        return start_date