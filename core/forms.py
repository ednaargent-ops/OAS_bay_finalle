import datetime

from django import forms
from django.core.validators import MaxLengthValidator

from .models import Customer, Vehicle

CURRENT_YEAR = datetime.date.today().year
YEAR_CHOICES = [('', '- Select year -')] + [
    (year, year) for year in range(CURRENT_YEAR + 1, 1979, -1)
]


class CustomerForm(forms.ModelForm):
    # Validators only (no max_length kwarg) so Django doesn't render an HTML
    # maxlength attribute — the browser would silently truncate input at that
    # point, so the length check must happen server-side, not in the markup.
    full_name = forms.CharField(
        validators=[MaxLengthValidator(30, message='Name must be at most 30 characters.')],
    )
    phone = forms.CharField(
        validators=[MaxLengthValidator(10, message='Phone number must be at most 10 characters.')],
    )

    class Meta:
        model = Customer
        fields = ['full_name', 'phone', 'email']


class VehicleForm(forms.ModelForm):
    year = forms.TypedChoiceField(
        choices=YEAR_CHOICES, coerce=int, required=False, empty_value=None,
    )

    class Meta:
        model = Vehicle
        fields = ['make', 'model', 'plate_number', 'duty_class', 'year']
