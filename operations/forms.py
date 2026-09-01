from django import forms
from django.contrib.auth import get_user_model

from inventory.models import Service, SparePart

from .models import JobCard, JobCardPartLine, JobCardServiceLine, Payment

User = get_user_model()


class JobCardForm(forms.ModelForm):
    class Meta:
        model = JobCard
        fields = ['vehicle', 'visit_type', 'diagnosis_notes', 'assigned_technicians']
        widgets = {'diagnosis_notes': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, customer=None, **kwargs):
        super().__init__(*args, **kwargs)
        if customer is not None:
            self.fields['vehicle'].queryset = customer.vehicles.all()
        self.fields['vehicle'].required = False
        self.fields['assigned_technicians'].queryset = User.objects.filter(
            groups__name__in=['Senior Technician', 'Junior Technician']
        ).distinct()
        self.fields['assigned_technicians'].required = False


class JobCardServiceLineForm(forms.ModelForm):
    class Meta:
        model = JobCardServiceLine
        fields = ['service']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['service'].queryset = Service.objects.filter(active=True)


class JobCardPartLineForm(forms.ModelForm):
    class Meta:
        model = JobCardPartLine
        fields = ['spare_part', 'quantity']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['spare_part'].queryset = SparePart.objects.filter(active=True)

    def clean(self):
        cleaned = super().clean()
        part = cleaned.get('spare_part')
        quantity = cleaned.get('quantity')
        if part and quantity and quantity > part.quantity_in_stock:
            raise forms.ValidationError(
                f'Only {part.quantity_in_stock} of {part.name} left in stock.'
            )
        return cleaned


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['amount', 'method']

    def __init__(self, *args, job_card=None, **kwargs):
        self.job_card = job_card
        super().__init__(*args, **kwargs)

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= 0:
            raise forms.ValidationError('Amount must be greater than zero.')
        if self.job_card is not None and amount > self.job_card.balance:
            raise forms.ValidationError(
                f'Amount exceeds balance of UGX {self.job_card.balance:,.0f}.'
            )
        return amount
