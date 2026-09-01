from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

from inventory.models import Service, SparePart
from operations.models import JobCard, JobCardPartLine, JobCardServiceLine, Payment

SERVICES = [
    ('Engine Oil Change', 20000),
    ('Gearbox Oil Change', 20000),
    ('Brake Fluid Change', 20000),
    ('Brake Pad Change', 20000),
    ('Greasing', 20000),
    ('Minor Repair', 20000),
    ('Wheel Alignment', 30000),
    ('Wheel Balancing', 20000),
]

SPARE_PARTS = [
    # name, category, cost_price, selling_price, quantity_in_stock, reorder_level
    ('Engine Oil', 'Oils', 65000, 95000, 30, 5),
    ('Gearbox Oil', 'Oils', 22000, 30000, 20, 5),
    ('Oil Filter', 'Filters', 12000, 18000, 25, 5),
    ('Gearbox Oil Filter', 'Filters', 38000, 50000, 15, 5),
    ('Brake Fluid', 'Brake Parts', 10000, 16000, 20, 5),
    ('Brake Pad', 'Brake Parts', 25000, 35000, 15, 5),
]

GROUP_PERMISSIONS = {
    'Admin': None,  # gets every permission on the three apps
    'Senior Technician': [
        ('core', 'customer', ['add', 'change', 'view']),
        ('core', 'vehicle', ['add', 'change', 'view']),
        ('inventory', 'service', ['view', 'change']),
        ('inventory', 'sparepart', ['view', 'change']),
        ('operations', 'jobcard', ['add', 'change', 'view']),
        ('operations', 'jobcardserviceline', ['add', 'change', 'view', 'delete']),
        ('operations', 'jobcardpartline', ['add', 'change', 'view', 'delete']),
        ('operations', 'payment', ['add']),
    ],
    'Junior Technician': [
        ('core', 'customer', ['view']),
        ('core', 'vehicle', ['view']),
        ('operations', 'jobcard', ['view', 'change']),
    ],
}


class Command(BaseCommand):
    help = 'Seed groups/permissions and the confirmed service/spare-part catalog.'

    def handle(self, *args, **options):
        self.seed_groups()
        self.seed_services()
        self.seed_spare_parts()
        self.stdout.write(self.style.SUCCESS('Seed data created.'))

    def seed_groups(self):
        all_models = [Service, SparePart, JobCard, JobCardServiceLine, JobCardPartLine, Payment]
        from core.models import Customer, Vehicle
        all_models += [Customer, Vehicle]

        admin_group, _ = Group.objects.get_or_create(name='Admin')
        all_perms = Permission.objects.filter(
            content_type__app_label__in=['core', 'inventory', 'operations']
        )
        admin_group.permissions.set(all_perms)

        for group_name, rules in GROUP_PERMISSIONS.items():
            if rules is None:
                continue
            group, _ = Group.objects.get_or_create(name=group_name)
            perms = []
            for app_label, model_name, actions in rules:
                for action in actions:
                    codename = f'{action}_{model_name}'
                    try:
                        perms.append(
                            Permission.objects.get(
                                content_type__app_label=app_label, codename=codename
                            )
                        )
                    except Permission.DoesNotExist:
                        self.stderr.write(f'Missing permission {app_label}.{codename}')
            group.permissions.set(perms)
            self.stdout.write(f'Group "{group_name}" configured with {len(perms)} permissions.')

        self.stdout.write(f'Group "Admin" configured with {all_perms.count()} permissions.')

    def seed_services(self):
        for name, price in SERVICES:
            Service.objects.get_or_create(name=name, defaults={'labor_price': price})
        self.stdout.write(f'{len(SERVICES)} services ensured.')

    def seed_spare_parts(self):
        for name, category, cost, price, qty, reorder in SPARE_PARTS:
            SparePart.objects.get_or_create(
                name=name,
                defaults={
                    'category': category,
                    'cost_price': cost,
                    'selling_price': price,
                    'quantity_in_stock': qty,
                    'reorder_level': reorder,
                },
            )
        self.stdout.write(f'{len(SPARE_PARTS)} spare parts ensured.')
