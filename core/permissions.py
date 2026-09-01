DASHBOARD_GROUPS = ['Admin', 'Senior Technician']


def can_view_dashboard(user):
    return user.is_superuser or user.groups.filter(name__in=DASHBOARD_GROUPS).exists()
