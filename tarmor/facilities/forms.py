from django import forms
from .models import CostCentre, Facility

class CostCentreUploadForm(forms.ModelForm):
    class Meta:
        model = CostCentre
        fields = [
            "Cost_Centre",
            "Cost_Centre_Description",
            "Status"
        ]
        widgets = {
            "Cost_Centre": forms.TextInput(attrs={"class": "input", "size": "10"}),
            "Cost_Centre_Description": forms.TextInput(attrs={"class": "input", "size": "60"}),
            "Status": forms.Select(attrs={"class": "input"})
        }
        labels = {
            "Cost_Centre": "Cost Center",
            "Cost_Centre_Description": "Description",
            "Status":"Status"
        }
        
class FacilityUploadForm(forms.ModelForm):
    class Meta:
        model = Facility
        fields = [
            "Facility_Code",
            "Facility_Name",
            "Cost_Centre",
            "Status",
            "Street_Address",
            "City",
            "Province_State",
            "Country",
            "Postal_Zip_Code",
            "Contact_Name",
            "Contact_Phone_Number",
            "Email_Address",
            "Additional_Information",
        ]
        widgets = {
            "Facility_Code": forms.TextInput(attrs={"class": "input", "size": "10"}),
            "Facility_Name": forms.TextInput(attrs={"class": "input", "size": "60"}),
            "Cost_Centre": forms.Select(attrs={"class": "input"}),
            "Status": forms.Select(attrs={"class": "input"}),
            "Street_Address": forms.TextInput(attrs={"class": "input", "size": "20"}),
            "City": forms.TextInput(attrs={"class": "input", "size": "20"}),
            "Province_State": forms.TextInput(attrs={"class": "input", "size": "4"}),
            "Country": forms.TextInput(attrs={"class": "input", "size": "25"}),
            "Postal_Zip_Code": forms.TextInput(attrs={"class": "input", "size": "10"}),
            "Contact_Name": forms.TextInput(attrs={"class": "input", "size": "60"}),
            "Contact_Phone_Number": forms.TextInput(attrs={"class": "input", "size": "25"}),
            "Email_Address": forms.TextInput(attrs={"class": "input", "size": "40"}),
            "Additional_Information": forms.Textarea(attrs={"class": "input", "rows": "6", "cols": "75"}),
        }
        labels = {
            "Facility_Code": "Facility Code",
            "Facility_Name": "Facility Name",
            "Cost_Centre": "Cost Center",
            "Status": "Status",
            "Street_Address": "Street Address",
            "Province_State": "Province / State",
            "Postal_Zip_Code": "Postal / Zip Code",
            "Contact_Name": "Contact Name",
            "Contact_Phone_Number": "Contact Phone Number",
            "Email_Address": "Email Address",
            "Additional_Information": "Additional Information",
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["Cost_Centre"].queryset = CostCentre.objects.order_by("Cost_Centre")
        self.fields["Country"].initial = "Canada"