from django import forms
from .models import MOCQuestionResponse, MOC, MOCQuestion, Safety, MOCConsiderations, MOCPro, MOCCon, MOCAttachment

class MOCQuestionResponseForm(forms.ModelForm):
    class Meta:
        model = MOCQuestionResponse
        fields = ["dropdown_answer", "detail", "complete"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'input'})

MOCQuestionResponseFormSet = forms.modelformset_factory(
    MOCQuestionResponse,
    form=MOCQuestionResponseForm,
    extra=0
)

class AddMOCForm(forms.ModelForm):
    class Meta:
        model = MOC
        fields = [
            "title",
            "define_change",
            "anticipated_outcome",
            "status",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "input"}),
            "status": forms.Select(attrs={"class": "input"}),
            "define_change": forms.Textarea(attrs={"class": "input", "rows": 4}),
            "anticipated_outcome": forms.Textarea(attrs={"class": "input", "rows": 4}),
        }

class EditMOCForm(forms.ModelForm):
    class Meta:
        model = MOC
        fields = [
            "title",
            "define_change",
            "anticipated_outcome",
            "status",
            "date_completed",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "input", "style": "width: 75%;"}),
            "status": forms.Select(attrs={"class": "input"}),
            "define_change": forms.Textarea(attrs={"class": "input", "rows": 4}),
            "anticipated_outcome": forms.Textarea(attrs={"class": "input", "rows": 4}),
            "date_completed": forms.DateInput(attrs={"class": "input", "type": "date"}),
        }

class MOCQuestionForm(forms.ModelForm):
    class Meta:
        model = MOCQuestion
        fields = ['section', 'text', 'order']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'input'})

MOCQuestionFormSet = forms.modelformset_factory(
    MOCQuestion, 
    form=MOCQuestionForm, 
    extra=1,
    can_delete=True
)

class SafetyForm(forms.ModelForm):
    class Meta:
        model = Safety
        fields = [
            "sh_risk",
            "sh_freq",
            "env_risk",
            "env_freq",
            "fin_risk",
            "fin_freq",
            "soc_risk",
            "soc_freq",
        ]
        widgets = {
            "sh_risk": forms.Select(attrs={"class": "input"}),
            "sh_freq": forms.Select(attrs={"class": "input"}),
            "env_risk": forms.Select(attrs={"class": "input"}),
            "env_freq": forms.Select(attrs={"class": "input"}),
            "fin_risk": forms.Select(attrs={"class": "input"}),
            "fin_freq": forms.Select(attrs={"class": "input"}),
            "soc_risk": forms.Select(attrs={"class": "input"}),
            "soc_freq": forms.Select(attrs={"class": "input"}),
        }

class ConsiderationsForm(forms.ModelForm):
    class Meta:
        model = MOCConsiderations
        fields = [
            "setup_months",
            "implementation_months",
            "contractor_hours",
            "eq_downtime",
            "warranty_impact",
            "project_cost",
            "savings_confirmed",
            "savings_soft",
            "inventory_cost",
            "production_gain",
            "safety_gain",
            "social_impact",
            "roi_months",
        ]
        widgets = {
            "setup_months": forms.Select(attrs={"class": "input"}),
            "implementation_months": forms.Select(attrs={"class": "input"}),
            "contractor_hours": forms.Select(attrs={"class": "input"}),
            "eq_downtime": forms.Select(attrs={"class": "input"}),
            "warranty_impact": forms.Select(attrs={"class": "input"}),
            "project_cost": forms.Select(attrs={"class": "input"}),
            "savings_confirmed": forms.Select(attrs={"class": "input"}),
            "savings_soft": forms.Select(attrs={"class": "input"}),
            "inventory_cost": forms.Select(attrs={"class": "input"}),
            "production_gain": forms.Select(attrs={"class": "input"}),
            "safety_gain": forms.Select(attrs={"class": "input"}),
            "social_impact": forms.Select(attrs={"class": "input"}),
            "roi_months": forms.Select(attrs={"class": "input"}),
        }

class ProsForm(forms.ModelForm):
    class Meta:
        model = MOCPro
        fields = ['text']
        widgets = {"text": forms.TextInput(attrs={"class": "input"})}

ProsFormSet = forms.modelformset_factory(
    MOCPro, 
    form=ProsForm, 
    extra=0,
    can_delete=True
)

class ConsForm(forms.ModelForm):
    class Meta:
        model = MOCCon
        fields = ['text']
        widgets = {"text": forms.TextInput(attrs={"class": "input"})}

ConsFormSet = forms.modelformset_factory(
    MOCCon, 
    form=ConsForm, 
    extra=0,
    can_delete=True
)

class AttachmentsForm(forms.ModelForm):
    class Meta:
        model = MOCAttachment
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
    MOCAttachment, 
    form=AttachmentsForm, 
    extra=0,
    can_delete=True
)