from django.db import models


class SubscriptionStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    TRIALING = "TRIALING", "Trialing"
    PAST_DUE = "PAST_DUE", "Past Due"
    CANCELED = "CANCELED", "Canceled"
    UNPAID = "UNPAID", "Unpaid"


class PlanType(models.TextChoices):
    FREE = "FREE", "Free"
    PRO = "PRO", "Pro"
    ENTERPRISE = "ENTERPRISE", "Enterprise"
