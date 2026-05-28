from django import forms
from django.forms import inlineformset_factory
from .models import Project, ProjectStep, ProjectDelay, ProjectAttachment, ProjectBudget, ProjectNote, ProjectLesson, ProjectFinancial, ProjectTasks

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = '__all__'
        exclude = ['remaining']
        widgets = {
            'scope': forms.Textarea(attrs={'rows': 5, 'style': 'width: 100%'}),
            'justification': forms.Textarea(attrs={'rows': 5, 'style': 'width: 100%'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'input'
            field.required = False

        if not self.instance.pk:
            self.initial['budget'] = 0.00
            self.initial['spend'] = 0.00
        
        if 'project_number' in self.fields:
            self.fields['project_number'].widget.attrs['readonly'] = True
            self.fields['project_number'].widget.attrs['class'] = 'locked'
            self.fields['project_number'].widget.attrs['placeholder'] = 'Auto-Generated'

AttachmentFormSet = inlineformset_factory(
    Project, 
    ProjectAttachment, 
    fields=('name', 'file'), 
    extra=1,
    can_delete=True,
    widgets = {
        'name': forms.TextInput(attrs={
            'class': 'input', 
            'placeholder': 'Enter name...',
            'style': 'flex-grow: 1;',
        }),
        "file": forms.FileInput(attrs={"class": "input"}),
    }
)

class ProjectStepForm(forms.ModelForm):
    class Meta:
        model = ProjectStep
        fields = '__all__'
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing_classes = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f'{existing_classes} input'.strip()

StepFormSet = inlineformset_factory(
    Project, 
    ProjectStep, 
    form=ProjectStepForm,
    fields='__all__', 
    extra=1,
    can_delete=True
    
)

class ProjectDelayForm(forms.ModelForm):
    class Meta:
        model = ProjectDelay
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'input'

        if self.instance and self.instance.project_id:
                self.fields['step'].queryset = ProjectStep.objects.filter(
                    project_id=self.instance.project_id
                ).order_by('step_number')

DelayFormSet = inlineformset_factory(
    Project, 
    ProjectDelay,
    form=ProjectDelayForm,
    fields='__all__', 
    extra=1
)

class ProjectBudgetForm(forms.ModelForm):
    class Meta:
        model = ProjectBudget
        fields = ['year', 'allocated_budget']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'input'
        
        if 'year' in self.fields:
            self.fields['year'].widget.attrs['readonly'] = True
            self.fields['year'].widget.attrs['class'] = 'locked'

BudgetFormSet = inlineformset_factory(
    Project, 
    ProjectBudget, 
    form=ProjectBudgetForm,
    extra=0, 
    can_delete=False
)

class ProjectNoteForm(forms.ModelForm):
    class Meta:
        model = ProjectNote
        fields = '__all__'
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'input'}),
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'input'}),
            'completed_date': forms.DateInput(attrs={'type': 'date', 'class': 'input'}),
            'action': forms.Textarea(attrs={'rows': 2, 'class': 'input'}),
            'step_note': forms.TextInput(attrs={'class': 'input'}),
            'progress': forms.Textarea(attrs={'rows': 2, 'class': 'input'}),
            'complete': forms.Select(attrs={'class': 'input'}),
        }

    def __init__(self, *args, **kwargs):
        project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'input'})
        
        if project:
            self.fields['step'].queryset = project.steps.all()

ProjectNoteFormSet = inlineformset_factory(
    Project, 
    ProjectNote, 
    form=ProjectNoteForm, 
    extra=1, 
    can_delete=True
)

class ProjectLessonForm(forms.ModelForm):
    class Meta:
        model = ProjectLesson
        fields = '__all__'
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'input'}),
            'lesson': forms.TextInput(attrs={'class': 'input'}),
            'completed_date': forms.DateInput(attrs={'type': 'date', 'class': 'input'}),
            'action': forms.Textarea(attrs={'rows': 2, 'class': 'input'}),
            'failure': forms.TextInput(attrs={'class': 'input'}),
            'progress': forms.Textarea(attrs={'rows': 2, 'class': 'input'}),
            'complete': forms.Select(attrs={'class': 'input'}),
        }

    def __init__(self, *args, **kwargs):
        project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'input'})
        
        if project:
            self.fields['step'].queryset = project.steps.all()

ProjectLessonFormSet = inlineformset_factory(
    Project, 
    ProjectLesson, 
    form=ProjectLessonForm, 
    extra=1, 
    can_delete=True
)

class ProjectFinancialForm(forms.ModelForm):
    class Meta:
        model = ProjectFinancial
        fields = '__all__'
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'input', 'style': 'width: 98%; text-align: center; box-sizing: border-box;'})

FinancialFormSet = inlineformset_factory(
    Project, 
    ProjectFinancial, 
    form=ProjectFinancialForm, 
    extra=0
)

class ProjectTasksForm(forms.ModelForm):
    class Meta:
        model = ProjectTasks
        fields = '__all__'
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'input'}),
            'task': forms.TextInput(attrs={'class': 'input'}),
            'completed_date': forms.DateInput(attrs={'type': 'date', 'class': 'input'}),
            'assignee': forms.TextInput(attrs={'class': 'input'}),
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'input'}),
            'progress': forms.Textarea(attrs={'rows': 2, 'class': 'input'}),
            'complete': forms.Select(attrs={'class': 'input'}),
        }

    def __init__(self, *args, **kwargs):
        project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'input'})
        
        if project:
            self.fields['step'].queryset = project.steps.all()

ProjectTasksFormSet = inlineformset_factory(
    Project, 
    ProjectTasks, 
    form=ProjectTasksForm, 
    extra=1, 
    can_delete=True
)

class ProjectPlanningForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['status', 'assigned_to', 'start_year']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs.update({'class': 'input'})