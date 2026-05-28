from django import forms
from django.forms import inlineformset_factory
from .models import Purchase, PurchaseLine, status_choices
from inventory.models import InventoryItem

class PurchaseForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = [
            'purchase_type',
            'date',
            'bill_location',
            'wo_cc',
            'project',
            'status',
            'additional_information',
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'input'}),
            'purchase_type': forms.Select(attrs={'class': 'input', 'id': 'id_purchase_type'}),
            'bill_location': forms.Select(attrs={'class': 'input', 'id': 'id_bill_location'}),
            'wo_cc': forms.TextInput(attrs={'class': 'input', 'id': 'id_wo_cc'}),
            'barcode': forms.TextInput(attrs={'class': 'input'}),
            'status': forms.Select(attrs={'class': 'input'}),
            'additional_information': forms.Textarea(attrs={'rows': 4, 'class': 'input', 'style': 'width: 90%'}),
        }

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
        
            for field in self.fields.values():
                field.widget.attrs['class'] = 'input'

            if self.initial.get('project') or (self.instance and self.instance.project):
                self.fields['project'].widget.attrs['class'] = 'locked'
        
class PurchaseLineForm(forms.ModelForm):
    inventory_item = forms.ModelChoiceField(
        queryset=InventoryItem.objects.all(), 
        required=False, 
        widget=forms.HiddenInput()
    )

    row_status = forms.ChoiceField(
        choices=status_choices,
        initial='Pending',
        widget=forms.Select(attrs={'class': 'input row-status'})
    )

    class Meta:
        model = PurchaseLine
        fields = [
            'inventory_item',
            'part_number_input',
            'manufacturer',
            'part_description',
            'uom',
            'supplier',
            'qty',
            'unit_price',
            'row_status',
        ]
        widgets = {
            'part_number_input': forms.TextInput(attrs={'class': 'input part-number-input', 'placeholder': 'Enter part number'}),
            'manufacturer': forms.TextInput(attrs={'class': 'input manufacturer'}),
            'part_description': forms.TextInput(attrs={'class': 'input part-description'}),
            'uom': forms.TextInput(attrs={'class': 'input uom'}),
            'supplier': forms.Select(attrs={'class': 'input supplier'}),
            'qty': forms.NumberInput(attrs={'class': 'input qty', 'step': '0.01'}),
            'unit_price': forms.NumberInput(attrs={'class': 'input unit-price', 'step': '0.01'}),

        }


PurchaseLineFormSet = inlineformset_factory(
    Purchase,
    PurchaseLine,
    form=PurchaseLineForm,
    extra=0,
    can_delete=True
)