from apps.billing.models import Plan


def get_active_plans():
    return Plan.objects.filter(
        is_active=True,
    ).order_by("price")
