from django.db import models
from equipment.models import Equipment

class RebuildPlanRow(models.Model):
    INTERVENTION_CHOICES = [
        ('Rebuild', 'Rebuild'),
        ('Replace', 'Replacement'),
    ]

    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='rebuild_plans')
    intervention_type = models.CharField(max_length=10, choices=INTERVENTION_CHOICES)
    intervention_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    calculated_year = models.IntegerField()
    modified_year = models.IntegerField(null=True, blank=True)
    
    project_number = models.CharField(max_length=50, null=True, blank=True)
    is_approved = models.BooleanField(default=False)
    is_complete = models.BooleanField(default=False)
    
    iteration_cycle = models.IntegerField(default=1)

    class Meta:
        db_table = 'reliability_rebuildplanrow'
        unique_together = ('equipment', 'calculated_year', 'intervention_type', 'iteration_cycle')

    def __str__(self):
        return f"{self.equipment.Equipment_Number} - {self.intervention_type} ({self.planned_year})"

    @property
    def planned_year(self):
        """Returns the execution target year: modified override if present, else original forecast."""
        return self.modified_year if self.modified_year else self.calculated_year