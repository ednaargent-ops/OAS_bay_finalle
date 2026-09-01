from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.shortcuts import get_object_or_404, redirect, render

from core.decorators import superuser_required

from .forms import ROLE_CHOICES, TechnicianCreateForm

User = get_user_model()
ROLE_NAMES = [name for name, _ in ROLE_CHOICES]


@superuser_required
def technician_list(request):
    technicians = (
        User.objects.filter(groups__name__in=ROLE_NAMES)
        .distinct()
        .prefetch_related('groups')
        .order_by('first_name', 'username')
    )
    return render(request, 'accounts/technician_list.html', {
        'technicians': technicians,
        'role_choices': ROLE_CHOICES,
    })


@superuser_required
def technician_create(request):
    if request.method == 'POST':
        form = TechnicianCreateForm(request.POST)
        if form.is_valid():
            role = form.cleaned_data['role']
            technician = form.save()
            group, _ = Group.objects.get_or_create(name=role)
            technician.groups.set([group])
            messages.success(
                request,
                f'{technician.get_full_name() or technician.username} added as {role}.',
            )
            return redirect('technician_list')
    else:
        form = TechnicianCreateForm()
    return render(request, 'accounts/technician_form.html', {'form': form})


@superuser_required
def technician_update(request, pk):
    technician = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        role = request.POST.get('role')
        if role in ROLE_NAMES:
            group, _ = Group.objects.get_or_create(name=role)
            technician.groups.set([group])
            technician.is_staff = role == 'Admin'
        technician.is_active = request.POST.get('is_active') == 'on'
        technician.save()
        messages.success(request, f'{technician.get_full_name() or technician.username} updated.')
    return redirect('technician_list')
