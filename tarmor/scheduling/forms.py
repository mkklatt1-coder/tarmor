from django import forms
from .models import WeekSetup

class WeekSetupForm(forms.ModelForm):
    class Meta:
        model = WeekSetup
        fields = ["start_day", "week1_start_date", "active"]
        widgets = {
            "week1_start_date": forms.DateInput(attrs={"class": "input", "type": "date"}),
            "start_day": forms.Select(attrs= {"class": "input"})
        }