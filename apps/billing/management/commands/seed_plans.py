from django.core.management.base import BaseCommand

from apps.billing.constants import PlanType
from apps.billing.models import Plan


class Command(BaseCommand):
    help = "Seed billing plans"

    def handle(self, *args, **kwargs):
        plans = [
            {
                "name": PlanType.FREE,
                "price": 0,
                "max_users": 5,
                "api_limit": 1000,
                "description": "Free Plan",
            },
            {
                "name": PlanType.PRO,
                "price": 29,
                "max_users": 25,
                "api_limit": 10000,
                "description": "Pro Plan",
            },
            {
                "name": PlanType.ENTERPRISE,
                "price": 99,
                "max_users": 100,
                "api_limit": 100000,
                "description": "Enterprise Plan",
            },
        ]

        for plan_data in plans:
            Plan.objects.update_or_create(
                name=plan_data["name"],
                defaults=plan_data,
            )

        self.stdout.write(self.style.SUCCESS("Plans seeded successfully."))
