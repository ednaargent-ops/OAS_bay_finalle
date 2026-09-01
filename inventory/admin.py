from django.contrib import admin

from .models import InventoryTransaction, Service, SparePart


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'labor_price', 'active')
    list_filter = ('active',)
    search_fields = ('name',)


@admin.register(SparePart)
class SparePartAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'category', 'compatibility', 'cost_price', 'selling_price',
        'quantity_in_stock', 'reorder_level', 'is_low_stock', 'active',
    )
    list_filter = ('category', 'active')
    search_fields = ('name', 'category', 'compatibility')

    @admin.display(boolean=True, description='Low stock')
    def is_low_stock(self, obj):
        return obj.is_low_stock

    def get_list_display(self, request):
        fields = super().get_list_display(request)
        if not request.user.is_superuser:
            fields = [f for f in fields if f != 'cost_price']
        return fields

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if not request.user.is_superuser:
            fields = [f for f in fields if f != 'cost_price']
        return fields


@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display = ('spare_part', 'type', 'quantity', 'unit_cost', 'reference', 'created_at')
    list_filter = ('type',)
