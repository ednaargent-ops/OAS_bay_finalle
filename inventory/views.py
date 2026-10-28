from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render

from core.permissions import can_view_cost_price

from .forms import RestockForm, ServiceForm, SparePartForm
from .models import InventoryTransaction, Service, SparePart


@login_required
@permission_required('inventory.view_sparepart', raise_exception=True)
def spare_part_list(request):
    query = request.GET.get('q', '').strip()
    parts = SparePart.objects.all().order_by('name')
    if query:
        parts = parts.filter(
            Q(name__icontains=query)
            | Q(category__icontains=query)
            | Q(compatibility__icontains=query)
        )

    paginator = Paginator(parts, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    querydict = request.GET.copy()
    querydict.pop('page', None)
    extra_qs = ('&' + querydict.urlencode()) if querydict else ''

    return render(request, 'inventory/spare_part_list.html', {
        'parts': page_obj, 'query': query, 'extra_qs': extra_qs,
        'show_cost': can_view_cost_price(request.user),
    })


@login_required
@permission_required('inventory.view_service', raise_exception=True)
def service_list(request):
    query = request.GET.get('q', '').strip()
    services = Service.objects.all().order_by('name')
    if query:
        services = services.filter(name__icontains=query)

    paginator = Paginator(services, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    querydict = request.GET.copy()
    querydict.pop('page', None)
    extra_qs = ('&' + querydict.urlencode()) if querydict else ''

    return render(request, 'inventory/service_list.html', {
        'services': page_obj, 'query': query, 'extra_qs': extra_qs,
    })


@login_required
@permission_required('inventory.add_service', raise_exception=True)
def service_create(request):
    if request.method == 'POST':
        form = ServiceForm(request.POST, user=request.user)
        if form.is_valid():
            service = form.save()
            messages.success(request, f'{service.name} added.')
            return redirect('service_list')
    else:
        form = ServiceForm(user=request.user)
    return render(request, 'inventory/service_form.html', {'form': form})


@login_required
@permission_required('inventory.change_service', raise_exception=True)
def service_edit(request, pk):
    service = get_object_or_404(Service, pk=pk)
    if request.method == 'POST':
        form = ServiceForm(request.POST, instance=service, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f'{service.name} updated.')
            return redirect('service_list')
    else:
        form = ServiceForm(instance=service, user=request.user)
    return render(request, 'inventory/service_form.html', {'form': form, 'service': service})


@login_required
@permission_required('inventory.change_sparepart', raise_exception=True)
def spare_part_edit(request, pk):
    part = get_object_or_404(SparePart, pk=pk)
    if request.method == 'POST':
        form = SparePartForm(request.POST, instance=part, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f'{part.name} updated.')
            return redirect('spare_part_list')
    else:
        form = SparePartForm(instance=part, user=request.user)
    return render(request, 'inventory/spare_part_form.html', {'form': form, 'part': part})


@login_required
@permission_required('inventory.delete_sparepart', raise_exception=True)
def spare_part_delete(request, pk):
    part = get_object_or_404(SparePart, pk=pk)
    if request.method == 'POST':
        name = part.name
        try:
            part.delete()
            messages.success(request, f'{name} deleted.')
        except ProtectedError:
            messages.error(
                request,
                f'Cannot delete {name} — it has already been used on a job card. '
                'Mark it inactive instead.',
            )
    return redirect('spare_part_list')


@login_required
@permission_required('inventory.delete_service', raise_exception=True)
def service_delete(request, pk):
    service = get_object_or_404(Service, pk=pk)
    if request.method == 'POST':
        name = service.name
        try:
            service.delete()
            messages.success(request, f'{name} deleted.')
        except ProtectedError:
            messages.error(
                request,
                f'Cannot delete {name} — it has already been used on a job card. '
                'Mark it inactive instead.',
            )
    return redirect('service_list')


@login_required
@permission_required('inventory.add_inventorytransaction', raise_exception=True)
def spare_part_restock(request):
    if request.method == 'POST':
        form = RestockForm(request.POST)
        if form.is_valid():
            part = form.cleaned_data['spare_part']
            quantity = form.cleaned_data['quantity']
            unit_cost = form.cleaned_data['unit_cost']

            InventoryTransaction.objects.create(
                spare_part=part,
                type=InventoryTransaction.RESTOCK,
                quantity=quantity,
                unit_cost=unit_cost,
            )
            part.quantity_in_stock += quantity
            part.cost_price = unit_cost
            part.save(update_fields=['quantity_in_stock', 'cost_price'])

            messages.success(
                request,
                f'Added {quantity} x {part.name} — UGX {quantity * unit_cost:,.0f} spent.',
            )
            return redirect('spare_part_list')
    else:
        form = RestockForm()
    return render(request, 'inventory/spare_part_restock_form.html', {'form': form})
