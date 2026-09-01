from datetime import timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from core.models import Customer
from core.permissions import can_view_dashboard
from inventory.models import SparePart

from .forms import JobCardForm, JobCardPartLineForm, JobCardServiceLineForm, PaymentForm
from .models import JobCard, JobCardPartLine, JobCardServiceLine, Payment


def _percent_change(current, previous):
    if not previous:
        return None
    return ((current - previous) / previous) * 100


@login_required
def dashboard(request):
    if not can_view_dashboard(request.user):
        return redirect('job_card_list')

    today = timezone.localdate()
    today_revenue = (
        Payment.objects.filter(paid_at__date=today).aggregate(total=Sum('amount'))['total']
        or Decimal('0')
    )
    open_job_cards = JobCard.objects.exclude(status=JobCard.PAID).count()
    low_stock = SparePart.objects.filter(active=True, quantity_in_stock__lt=10).order_by('quantity_in_stock')
    top_services = (
        JobCardServiceLine.objects.values('service__name')
        .annotate(count=Count('id'))
        .order_by('-count')[:5]
    )

    month_start = today.replace(day=1)
    prev_month_end = month_start - timedelta(days=1)
    prev_month_start = prev_month_end.replace(day=1)

    total_customers = Customer.objects.count()
    new_customers_this_month = Customer.objects.filter(created_at__date__gte=month_start).count()
    new_customers_last_month = Customer.objects.filter(
        created_at__date__gte=prev_month_start, created_at__date__lte=prev_month_end
    ).count()
    customer_growth = _percent_change(new_customers_this_month, new_customers_last_month)

    total_revenue = Payment.objects.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    revenue_this_month = (
        Payment.objects.filter(paid_at__date__gte=month_start)
        .aggregate(total=Sum('amount'))['total']
        or Decimal('0')
    )
    revenue_last_month = (
        Payment.objects.filter(
            paid_at__date__gte=prev_month_start, paid_at__date__lte=prev_month_end
        ).aggregate(total=Sum('amount'))['total']
        or Decimal('0')
    )
    revenue_growth = _percent_change(revenue_this_month, revenue_last_month)

    # Trailing 6 months, oldest first, for the growth charts.
    months = []
    cursor = month_start
    for _ in range(6):
        months.insert(0, cursor)
        cursor = (cursor.replace(day=1) - timedelta(days=1)).replace(day=1)
    range_start = months[0]

    customers_by_month = {
        row['month'].date(): row['count']
        for row in (
            Customer.objects.filter(created_at__date__gte=range_start)
            .annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(count=Count('id'))
        )
    }
    revenue_by_month = {
        row['month'].date(): row['total']
        for row in (
            Payment.objects.filter(paid_at__date__gte=range_start)
            .annotate(month=TruncMonth('paid_at'))
            .values('month')
            .annotate(total=Sum('amount'))
        )
    }

    growth_labels = [m.strftime('%b %Y') for m in months]
    new_customers_series = [customers_by_month.get(m, 0) for m in months]
    revenue_series = [float(revenue_by_month.get(m) or 0) for m in months]

    return render(request, 'operations/dashboard.html', {
        'today_revenue': today_revenue,
        'open_job_cards': open_job_cards,
        'low_stock': low_stock,
        'top_services': top_services,
        'total_customers': total_customers,
        'new_customers_this_month': new_customers_this_month,
        'customer_growth': customer_growth,
        'total_revenue': total_revenue,
        'revenue_this_month': revenue_this_month,
        'revenue_growth': revenue_growth,
        'growth_labels': growth_labels,
        'new_customers_series': new_customers_series,
        'revenue_series': revenue_series,
    })


@login_required
@permission_required('operations.view_jobcard', raise_exception=True)
def job_card_list(request):
    status = request.GET.get('status', '')
    query = request.GET.get('q', '').strip()
    job_cards = JobCard.objects.select_related('customer', 'vehicle').order_by('-created_at')
    if status:
        job_cards = job_cards.filter(status=status)
    if query:
        job_cards = job_cards.filter(
            Q(customer__full_name__icontains=query)
            | Q(customer__phone__icontains=query)
            | Q(vehicle__plate_number__icontains=query)
        ).distinct()

    paginator = Paginator(job_cards, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    querydict = request.GET.copy()
    querydict.pop('page', None)
    extra_qs = ('&' + querydict.urlencode()) if querydict else ''

    return render(request, 'operations/job_card_list.html', {
        'job_cards': page_obj,
        'status': status,
        'status_choices': JobCard.STATUS_CHOICES,
        'query': query,
        'extra_qs': extra_qs,
    })


PAYMENT_STATUS_CHOICES = [
    ('unpaid', 'Unpaid'),
    ('partial', 'Partially paid'),
    ('paid', 'Fully paid'),
]


@login_required
@permission_required('operations.view_payment', raise_exception=True)
def payment_list(request):
    payment_status = request.GET.get('status', '')
    query = request.GET.get('q', '').strip()

    job_cards = (
        JobCard.objects.select_related('customer', 'vehicle')
        .prefetch_related('service_lines', 'part_lines', 'payments')
        .order_by('-created_at')
    )
    if query:
        job_cards = job_cards.filter(
            Q(customer__full_name__icontains=query)
            | Q(customer__phone__icontains=query)
            | Q(vehicle__plate_number__icontains=query)
        ).distinct()

    job_cards = list(job_cards)
    if payment_status:
        job_cards = [jc for jc in job_cards if jc.payment_status == payment_status]

    total_outstanding = sum((jc.balance for jc in job_cards), Decimal('0'))

    paginator = Paginator(job_cards, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    querydict = request.GET.copy()
    querydict.pop('page', None)
    extra_qs = ('&' + querydict.urlencode()) if querydict else ''

    return render(request, 'operations/payment_list.html', {
        'job_cards': page_obj,
        'payment_status': payment_status,
        'payment_status_choices': PAYMENT_STATUS_CHOICES,
        'query': query,
        'extra_qs': extra_qs,
        'total_outstanding': total_outstanding,
    })


@login_required
@permission_required('operations.add_jobcard', raise_exception=True)
def job_card_create(request, customer_pk):
    customer = get_object_or_404(Customer, pk=customer_pk)
    initial = {}
    vehicle_id = request.GET.get('vehicle')
    if vehicle_id:
        initial['vehicle'] = vehicle_id

    if request.method == 'POST':
        form = JobCardForm(request.POST, customer=customer)
        if form.is_valid():
            job_card = form.save(commit=False)
            job_card.customer = customer
            job_card.diagnosed_by = request.user
            job_card.save()
            form.save_m2m()
            messages.success(request, 'Job card opened.')
            return redirect('job_card_detail', pk=job_card.pk)
    else:
        form = JobCardForm(customer=customer, initial=initial)
    return render(request, 'operations/job_card_form.html', {'form': form, 'customer': customer})


@login_required
@permission_required('operations.view_jobcard', raise_exception=True)
def job_card_detail(request, pk):
    job_card = get_object_or_404(JobCard, pk=pk)
    context = {
        'job_card': job_card,
        'service_form': JobCardServiceLineForm(),
        'part_form': JobCardPartLineForm(),
        'payment_form': PaymentForm(job_card=job_card),
    }
    return render(request, 'operations/job_card_detail.html', context)


@login_required
@permission_required('operations.add_jobcardserviceline', raise_exception=True)
def job_card_add_service(request, pk):
    job_card = get_object_or_404(JobCard, pk=pk)
    if request.method == 'POST':
        form = JobCardServiceLineForm(request.POST)
        if form.is_valid():
            line = form.save(commit=False)
            line.job_card = job_card
            line.save()
            messages.success(request, f'{line.service.name} added.')
        else:
            messages.error(request, 'Could not add that service.')
    return redirect('job_card_detail', pk=pk)


@login_required
@permission_required('operations.delete_jobcardserviceline', raise_exception=True)
def job_card_remove_service(request, pk):
    line = get_object_or_404(JobCardServiceLine, pk=pk)
    job_card_pk = line.job_card_id
    if request.method == 'POST':
        name = line.service.name
        line.delete()
        messages.success(request, f'{name} removed.')
    return redirect('job_card_detail', pk=job_card_pk)


@login_required
@permission_required('operations.add_jobcardpartline', raise_exception=True)
def job_card_add_part(request, pk):
    job_card = get_object_or_404(JobCard, pk=pk)
    if request.method == 'POST':
        form = JobCardPartLineForm(request.POST)
        if form.is_valid():
            line = form.save(commit=False)
            line.job_card = job_card
            line.save()
            messages.success(request, f'{line.quantity} x {line.spare_part.name} added.')
        else:
            for error in form.non_field_errors():
                messages.error(request, error)
    return redirect('job_card_detail', pk=pk)


@login_required
@permission_required('operations.delete_jobcardpartline', raise_exception=True)
def job_card_remove_part(request, pk):
    line = get_object_or_404(JobCardPartLine, pk=pk)
    job_card_pk = line.job_card_id
    if request.method == 'POST':
        name = line.spare_part.name
        line.delete()
        messages.success(request, f'{name} removed and stock restored.')
    return redirect('job_card_detail', pk=job_card_pk)


@login_required
@permission_required('operations.add_payment', raise_exception=True)
def job_card_add_payment(request, pk):
    job_card = get_object_or_404(JobCard, pk=pk)
    if request.method == 'POST':
        form = PaymentForm(request.POST, job_card=job_card)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.job_card = job_card
            payment.received_by = request.user
            payment.save()
            if job_card.balance <= 0:
                job_card.status = JobCard.PAID
                job_card.save(update_fields=['status'])
            messages.success(request, f'Payment of UGX {payment.amount:,.0f} recorded.')
            return redirect('receipt', pk=payment.pk)
        for error in form.errors.get('amount', []):
            messages.error(request, error)
    return redirect('job_card_detail', pk=pk)


@login_required
@permission_required('operations.change_jobcard', raise_exception=True)
def job_card_update_status(request, pk):
    job_card = get_object_or_404(JobCard, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(JobCard.STATUS_CHOICES):
            job_card.status = new_status
            if new_status == JobCard.COMPLETED and not job_card.completed_at:
                job_card.completed_at = timezone.now()
            job_card.save()
            messages.success(request, 'Status updated.')
    return redirect('job_card_detail', pk=pk)


@login_required
def receipt(request, pk):
    # Whoever can record a payment should be able to view/print the receipt
    # they just created, even without the broader payment-ledger permission.
    if not (request.user.has_perm('operations.view_payment')
            or request.user.has_perm('operations.add_payment')):
        raise PermissionDenied
    payment = get_object_or_404(Payment, pk=pk)
    return render(request, 'operations/receipt.html', {
        'payment': payment,
        'job_card': payment.job_card,
    })
