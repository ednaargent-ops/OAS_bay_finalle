from django.contrib import admin

from .models import JobCard, JobCardPartLine, JobCardServiceLine, Payment


class JobCardServiceLineInline(admin.TabularInline):
    model = JobCardServiceLine
    extra = 1


class JobCardPartLineInline(admin.TabularInline):
    model = JobCardPartLine
    extra = 1


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 1


@admin.register(JobCard)
class JobCardAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'vehicle', 'visit_type', 'status', 'created_at')
    list_filter = ('visit_type', 'status')
    search_fields = ('customer__full_name', 'vehicle__plate_number')
    filter_horizontal = ('assigned_technicians',)
    inlines = [JobCardServiceLineInline, JobCardPartLineInline, PaymentInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('job_card', 'amount', 'method', 'received_by', 'paid_at')
    list_filter = ('method',)
