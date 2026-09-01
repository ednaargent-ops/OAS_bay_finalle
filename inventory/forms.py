from django import forms

from .models import Service, SparePart


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['name', 'labor_price', 'active']

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None and not user.has_perm('inventory.change_service_price'):
            del self.fields['labor_price']


class SparePartForm(forms.ModelForm):
    class Meta:
        model = SparePart
        fields = [
            'name', 'category', 'compatibility', 'cost_price',
            'selling_price', 'reorder_level', 'active',
        ]

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            if not user.is_superuser:
                del self.fields['cost_price']
            if not user.has_perm('inventory.change_sparepart_price'):
                del self.fields['selling_price']


class RestockForm(forms.Form):
    spare_part = forms.ModelChoiceField(queryset=SparePart.objects.filter(active=True))
    quantity = forms.IntegerField(min_value=1)
    unit_cost = forms.DecimalField(
        min_value=0, max_digits=10, decimal_places=2,
        label='Cost price per unit (UGX)',
        help_text='What you paid the supplier per unit — updates the part\'s cost price.',
    )
