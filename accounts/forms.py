from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()

ROLE_CHOICES = [
    ('Admin', 'Admin'),
    ('Senior Technician', 'Senior Technician'),
    ('Junior Technician', 'Junior Technician'),
]


class TechnicianCreateForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput,
        help_text='Temporary password — they can change it after logging in.',
    )
    role = forms.ChoiceField(choices=ROLE_CHOICES)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.is_staff = self.cleaned_data['role'] == 'Admin'
        if commit:
            user.save()
        return user
