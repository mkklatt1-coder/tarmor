from django.db import models
from django.core.exceptions import ValidationError

ASSET_CHOICES = [
    ('', 'Select'),
    ('F', 'F'),
    ('M', 'M'),
]

class System(models.Model):
    asset_key = models.CharField(max_length=1, choices=ASSET_CHOICES)
    system_name = models.CharField(max_length=50)
    system_key = models.CharField(max_length=3)
    combined_sys_key = models.CharField(max_length=4, unique=True)
    
    def clean(self):
        if self.asset_key:
            self.asset_key = self.asset_key.upper().strip()
        if self.system_key:
            self.system_key = self.system_key.upper().strip()
        if len(self.asset_key or "") != 1:
            raise ValidationError({"asset_key": "Asset key must be 1 character."})
        if len(self.system_key or "") != 3:
            raise ValidationError({"system_key": "System key must be 3 characters."})
        self.combined_sys_key = f"{self.asset_key}{self.system_key}"
        qs = System.objects.filter(combined_sys_key=self.combined_sys_key)
        if self.pk:
            qs = qs.exclude(pk=self.pk)
        if qs.exists():
            raise ValidationError({
                "system_key": "This combined system code already exists."
            })
            
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        
    def __str__(self):
        return self.system_name

class Component(models.Model):
    component_name = models.CharField(max_length=50)
    component_key = models.CharField(max_length=4)
    combined_sys_key = models.ForeignKey(System, on_delete=models.CASCADE)
    combined_comp_key = models.CharField(max_length=8, unique=True)
    
    def save(self, *args, **kwargs):
        combined_comp_key = f"{self.combined_sys_key}{self.component_key}"
        
        if len(combined_comp_key) != 8:
            raise ValidationError("Final code must be exactly 8 characters.")
        
        self.full_code = combined_comp_key
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.component_name
        
class FailureType(models.Model):
    failure_mode = models.CharField(max_length=50)
    failure_code = models.CharField(max_length=3)
    
    def __str__(self):
        return self.failure_mode
    
class Action(models.Model):
    action_name = models.CharField(max_length=50)
    action_key = models.CharField(max_length=3)
    
    def __str__(self):
        return self.action_name