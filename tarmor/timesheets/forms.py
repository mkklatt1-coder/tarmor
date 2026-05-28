from django import forms
from .models import Timesheet
from personnel.models import Employee

class DateTimeLocalInput(forms.DateTimeInput):
    input_type = 'datetime-local'
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('format', '%Y-%m-%dT%H:%M')
        super().__init__(*args, **kwargs)
        self.attrs.setdefault('step', 60)
    
        
class TimesheetAddForm(forms.ModelForm):
    class Meta:
        model = Timesheet
        fields = [
            'work_order',
            'technician',
            'start_date',
            'finish_date',
            'total_time',
            'time_type',
        ]
        widgets = {
            'start_date': DateTimeLocalInput(attrs={'step': '900'}),
            'finish_date': DateTimeLocalInput(attrs={'step': '900'}),
            'total_time': forms.NumberInput(attrs={'readonly': 'readonly', 'class': 'locked input'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if 'total_time' in self.fields:
            self.fields['total_time'].required = False
            
        self.fields['work_order'].queryset = self.fields['work_order'].queryset.all()   
         
        if self.data.get('technician'):
            t_id = self.data.get('technician')
            self.fields['technician'].queryset = Employee.objects.filter(pk=t_id)
        elif self.instance.pk:
            self.fields['technician'].queryset = Employee.objects.filter(pk=self.instance.technician_id)
        else:
            self.fields['technician'].queryset = Employee.objects.all()
                
            self.fields['total_time'].widget.attrs.update({
                'readonly': 'readonly', 
                'class': 'locked input'
            })
            
        for name, field in self.fields.items():
            existing_classes = field.widget.attrs.get('class', '')
            if 'input' not in existing_classes.split():
                field.widget.attrs['class'] = f'{existing_classes} input'.strip()
                
        for field_name in ['start_date', 'finish_date']:
            self.fields[field_name].widget.attrs['step'] = '900'
            self.fields[field_name].input_formats = [
                '%Y-%m-%dT%H:%M',
                '%Y-%m-%d %H:%M',
                '%m/%d/%Y %H:%M',
                '%m/%d/%Y %I:%M %p',
            ]
        print("WORK ORDER QUERYSET COUNT:", self.fields['work_order'].queryset.count())
        print("INITIAL WORK ORDER:", self.initial.get('work_order'))
        print("POST WORK ORDER:", self.data.get('work_order'))

class TimesheetEditForm(forms.ModelForm):
    class Meta:
        model = Timesheet
        fields = [
            'work_order',
            'technician',
            'start_date',
            'finish_date',
            'total_time',
            'time_type',
        ]
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'input', 'step': '900'}),
            'finish_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'input', 'step': '900'}),
            'total_time': forms.NumberInput(attrs={'readonly': 'readonly', 'class': 'locked input'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ['start_date', 'finish_date']:
            self.fields[field_name].input_formats = [
                '%Y-%m-%dT%H:%M',
                '%Y-%m-%d %H:%M',
                '%m/%d/%Y %H:%M',
                '%m/%d/%Y %I:%M %p',
            ]
            
        for name, field in self.fields.items():
            existing_classes = field.widget.attrs.get('class', '')
            field.widget.attrs.update({'class': f'{existing_classes} input'.strip()})
        
            self.fields['total_time'].widget.attrs.update({
                'readonly': 'readonly', 
                'class': 'locked input'
            })
            