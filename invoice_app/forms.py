from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
from .models import Invoice, InvoiceOwner, InvoiceItem

class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['client', 'invoice_owner', 'tax_percentage']
        widgets = {
            'tax_percentage': forms.NumberInput(attrs={
                'min': '0',
                'max': '99999',
                'step': '0.1',
                'placeholder': 'Enter tax percentage (without "%")',
            })
        }

class InvoiceOwnerCreationForm(UserCreationForm):
    class Meta:
        model = InvoiceOwner
        fields = ("email", "ntn_number", "name", 'phone', 'address',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].required = True
        self.fields['ntn_number'].required = True
        self.fields['phone'].required = True
  

class InvoiceOwnerChangeForm(UserChangeForm):
    class Meta:
        model = InvoiceOwner
        fields = ("email", "ntn_number", "name", 'phone', 'address',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].required = True
        self.fields['ntn_number'].required = True
        self.fields['phone'].required = True


class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ['description', 'quantity', 'unit_price']
        widgets = {
            'quantity': forms.NumberInput(attrs={
                'min': '0',
                'max': '999999',
                'step': '1',
                'placeholder': 'Enter quantity'
            }),
            'unit_price': forms.NumberInput(attrs={
                'min': '0',
                'step': '10',  # Use 0.01 for decimal precision
                'placeholder': 'Enter unit price'
            }),
        }

    description = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Enter item description'})
    )


InvoiceItemFormSet = forms.inlineformset_factory(
    Invoice, InvoiceItem, form=InvoiceItemForm, extra=1
)