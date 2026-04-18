from django.forms import ModelForm, inlineformset_factory
from django import forms
from .models import MeterReading

class MeterUploadForm(forms.ModelForm):
    reading_diff = forms.IntegerField(required=False, label="Add Units",
        widget=forms.NumberInput(attrs={'class': 'input', 'placeholder': 'Enter Difference'}))
    
    Date = forms.DateField(required=False, 
        widget=forms.DateInput(attrs={'class': 'input', 'type': 'date'}))

    class Meta:
        model = MeterReading
        # We only let the user touch these two; the rest is calculated
        fields = ['Date', 'Meter_Reading', 'reading_diff', 'Meter_Replaced']
        widgets = {
            'Meter_Reading': forms.NumberInput(attrs={'class': 'input', 'placeholder': 'Current Reading'}),
            'Meter_Replaced': forms.Select(attrs={'class': 'input'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        reading = cleaned_data.get('Meter_Reading')
        diff = cleaned_data.get('reading_diff')

        # Validation: Ensure they didn't leave BOTH empty
        if reading is None and diff is None:
            raise forms.ValidationError("Please enter either a New Reading or a Difference.")

        return cleaned_data
    
