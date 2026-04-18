from django import forms
from .models import Supplier

class NewSupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ('supplier_name', 'status', 'street_address', 'city', 'province_state', 'country', 'postal_zip',
                  'contact', 'phone', 'email', 'supplier_discount', 'payment_method',
                  'supplier_currency', 'additional_information')
        widgets = {
            'additional_information': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for _, field in self.fields.items():
            field.widget.attrs.update({'class': 'input'})
            
    def clean_email(self):
        email = self.cleaned_data.get('email')
        return email or None
