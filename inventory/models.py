from django.db import models


class Service(models.Model):
    name = models.CharField(max_length=100, unique=True)
    labor_price = models.DecimalField(max_digits=10, decimal_places=2)
    active = models.BooleanField(default=True)

    class Meta:
        permissions = [
            ('change_service_price', 'Can change service labor price'),
        ]

    def __str__(self):
        return self.name


class SparePart(models.Model):
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=100, blank=True)
    compatibility = models.CharField(
        max_length=200, blank=True,
        help_text='Vehicle makes/models this part fits, e.g. "Toyota, Mercedes-Benz" '
                   'or "Toyota Hilux". Leave blank if it fits all vehicles.',
    )
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_in_stock = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=5)
    active = models.BooleanField(default=True)

    class Meta:
        permissions = [
            ('change_sparepart_price', 'Can change spare part selling price'),
        ]

    def __str__(self):
        return self.name

    @property
    def is_low_stock(self):
        return self.quantity_in_stock <= self.reorder_level


class InventoryTransaction(models.Model):
    RESTOCK = 'restock'
    USED = 'used'
    TYPE_CHOICES = [
        (RESTOCK, 'Restock'),
        (USED, 'Used'),
    ]

    spare_part = models.ForeignKey(SparePart, on_delete=models.CASCADE, related_name='transactions')
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    quantity = models.PositiveIntegerField()
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    reference = models.ForeignKey(
        'operations.JobCard', on_delete=models.SET_NULL, null=True, blank=True, related_name='inventory_transactions'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.get_type_display()} {self.quantity} x {self.spare_part.name}'
