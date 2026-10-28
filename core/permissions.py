DASHBOARD_GROUPS = ['Admin', 'Senior Technician']


def can_view_dashboard(user):
    return user.is_superuser or user.groups.filter(name__in=DASHBOARD_GROUPS).exists()


COST_PRICE_GROUPS = ['Admin']


def can_view_cost_price(user):
    return user.is_superuser or user.groups.filter(name__in=COST_PRICE_GROUPS).exists()
