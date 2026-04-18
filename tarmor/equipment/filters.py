import django_filters
from ..equipment.models import Equipment

class EquipmentFilter(django_filters.FilterSet):
    class Meta:
        model = Equipment
        fields = ['Equipment_Number', 'Asset_Type', 'Equipment_Type', 'Equipment_Status', 'Make', 'Model'] 