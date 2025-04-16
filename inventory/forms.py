from django import forms
from .models import Shelf, InventoryItem, Acquisition

class ShelfForm(forms.ModelForm):
    class Meta:
        model = Shelf
        fields = ['name', 'location', 'capacity', 'description', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class InventoryItemForm(forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = ['book', 'shelf', 'quantity', 'minimum_quantity',
                 'condition', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

class AcquisitionForm(forms.ModelForm):
    class Meta:
        model = Acquisition
        fields = ['book', 'quantity', 'acquisition_type', 'cost',
                 'supplier', 'invoice_number', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

class InventorySearchForm(forms.Form):
    search = forms.CharField(required=False)
    condition = forms.ChoiceField(
        choices=[('', '---')] + InventoryItem.CONDITION_CHOICES,
        required=False
    )
    needs_restock = forms.BooleanField(required=False)