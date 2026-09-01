from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CustomerForm, VehicleForm
from .models import Customer, Vehicle


@login_required
@permission_required('core.view_customer', raise_exception=True)
def customer_list(request):
    query = request.GET.get('q', '').strip()
    customers = Customer.objects.all().order_by('full_name')
    if query:
        customers = customers.filter(
            Q(full_name__icontains=query)
            | Q(phone__icontains=query)
            | Q(vehicles__plate_number__icontains=query)
        ).distinct()

    paginator = Paginator(customers, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    querydict = request.GET.copy()
    querydict.pop('page', None)
    extra_qs = ('&' + querydict.urlencode()) if querydict else ''

    return render(request, 'core/customer_list.html', {
        'customers': page_obj, 'query': query, 'extra_qs': extra_qs,
    })


@login_required
@permission_required('core.add_customer', raise_exception=True)
def customer_create(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            return redirect('customer_detail', pk=customer.pk)
    else:
        form = CustomerForm()
    return render(request, 'core/customer_form.html', {'form': form})


@login_required
@permission_required('core.view_customer', raise_exception=True)
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    return render(request, 'core/customer_detail.html', {'customer': customer})


@login_required
@permission_required('core.add_vehicle', raise_exception=True)
def vehicle_create(request, customer_pk):
    customer = get_object_or_404(Customer, pk=customer_pk)
    if request.method == 'POST':
        form = VehicleForm(request.POST)
        if form.is_valid():
            vehicle = form.save(commit=False)
            vehicle.customer = customer
            vehicle.save()
            return redirect('customer_detail', pk=customer.pk)
    else:
        form = VehicleForm()
    return render(request, 'core/vehicle_form.html', {'form': form, 'customer': customer})


@login_required
@permission_required('core.view_vehicle', raise_exception=True)
def vehicle_detail(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    return render(request, 'core/vehicle_detail.html', {'vehicle': vehicle})
