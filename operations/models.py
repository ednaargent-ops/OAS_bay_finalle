from django.conf import settings
from django.db import models

from core.models import Customer, Vehicle
from inventory.models import Service, SparePart


class JobCard(models.Model):
    SERVICE = 'service'
    PARTS = 'parts'
    BOTH = 'both'
    VISIT_TYPE_CHOICES = [
        (SERVICE, 'Service only'),
        (PARTS, 'Parts only'),
        (BOTH, 'Service and parts'),
    ]

    OPEN = 'open'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    PAID = 'paid'
    STATUS_CHOICES = [
        (OPEN, 'Open'),
        (IN_PROGRESS, 'In progress'),
        (COMPLETED, 'Completed'),
        (PAID, 'Paid'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='job_cards')
    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.PROTECT, null=True, blank=True, related_name='job_cards'
    )
    visit_type = models.CharField(max_length=10, choices=VISIT_TYPE_CHOICES, default=SERVICE)
    diagnosis_notes = models.TextField(blank=True)
    diagnosed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='diagnosed_job_cards',
    )
    assigned_technicians = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name='assigned_job_cards',
    )
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default=OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'Job Card #{self.pk} — {self.customer.full_name}'

    @property
    def total(self):
        service_total = sum((line.price_charged for line in self.service_lines.all()), start=0)
        part_total = sum(
            (line.price_charged * line.quantity for line in self.part_lines.all()), start=0
        )
        return service_total + part_total

    @property
    def amount_paid(self):
        return sum((p.amount for p in self.payments.all()), start=0)

    @property
    def balance(self):
        return self.total - self.amount_paid

    PAYMENT_STATUS_LABELS = {
        'unpaid': 'Unpaid',
        'partial': 'Partially paid',
        'paid': 'Fully paid',
    }

    @property
    def payment_status(self):
        total = self.total
        paid = self.amount_paid
        if paid <= 0:
            return 'unpaid'
        if total > 0 and paid >= total:
            return 'paid'
        return 'partial'

    def get_payment_status_display(self):
        return self.PAYMENT_STATUS_LABELS[self.payment_status]


class JobCardServiceLine(models.Model):
    job_card = models.ForeignKey(JobCard, on_delete=models.CASCADE, related_name='service_lines')
    service = models.ForeignKey(Service, on_delete=models.PROTECT)
    price_charged = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        if not self.price_charged:
            self.price_charged = self.service.labor_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.service.name} on Job Card #{self.job_card_id}'


class JobCardPartLine(models.Model):
    job_card = models.ForeignKey(JobCard, on_delete=models.CASCADE, related_name='part_lines')
    spare_part = models.ForeignKey(SparePart, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    price_charged = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        if not self.price_charged:
            self.price_charged = self.spare_part.selling_price
        super().save(*args, **kwargs)
        if is_new:
            from inventory.models import InventoryTransaction
            self.spare_part.quantity_in_stock = max(
                0, self.spare_part.quantity_in_stock - self.quantity
            )
            self.spare_part.save(update_fields=['quantity_in_stock'])
            InventoryTransaction.objects.create(
                spare_part=self.spare_part,
                type=InventoryTransaction.USED,
                quantity=self.quantity,
                reference=self.job_card,
            )

    def delete(self, *args, **kwargs):
        self.spare_part.quantity_in_stock += self.quantity
        self.spare_part.save(update_fields=['quantity_in_stock'])
        super().delete(*args, **kwargs)

    def __str__(self):
        return f'{self.quantity} x {self.spare_part.name} on Job Card #{self.job_card_id}'


class Payment(models.Model):
    CASH = 'cash'
    MTN_MOBILE_MONEY = 'mtn_mobile_money'
    AIRTEL_MONEY = 'airtel_money'
    METHOD_CHOICES = [
        (CASH, 'Cash'),
        (MTN_MOBILE_MONEY, 'MTN Mobile Money'),
        (AIRTEL_MONEY, 'Airtel Money'),
    ]

    job_card = models.ForeignKey(JobCard, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default=CASH)
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    paid_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'UGX {self.amount} for Job Card #{self.job_card_id}'
