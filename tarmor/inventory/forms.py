from django import forms
from .models import InventoryItem
from django.forms import modelformset_factory

class InventoryItemForm(forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = ['part_number', 'part_description', 'supplier', 'manufacturer', 
                  'qty', 'uom', 'unit_price', 'stock', 'controlled_product', 'bin_location', 'qty_onhand', 'min_qty', 'max_qty',
                  'last_transaction_date', 'last_transaction_number']

    def clean(self):
        cleaned_data = super().clean()
        part_num = cleaned_data.get('part_number')
        mfg = cleaned_data.get('manufacturer')

        if InventoryItem.objects.filter(part_number=part_num, manufacturer=mfg).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(f"Part {part_num} already exists for {mfg}.")
        return cleaned_data
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for _, field in self.fields.items():
            field.widget.attrs.update({'class': 'input'})
            
AlternativeFormSet = modelformset_factory(
        InventoryItem, 
        form=InventoryItemForm, 
        extra=0, 
        can_delete=True 
    )

