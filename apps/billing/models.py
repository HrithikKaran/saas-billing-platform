# apps/billing/models.py
from django.db import models

from apps.billing.constants import PlanType, SubscriptionStatus
from apps.common.models import TimeStampedModel, UUIDModel


class Plan(UUIDModel, TimeStampedModel):
    name = models.CharField(
        max_length=50,
        choices=PlanType.choices,
        unique=True,
    )

    description = models.TextField(blank=True)

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    max_users = models.PositiveIntegerField(default=0)

    api_limit = models.PositiveIntegerField(default=0)

    stripe_price_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "billing_plans"
        ordering = ["price"]

    def __str__(self):
        return self.name


class Subscription(UUIDModel, TimeStampedModel):
    organization = models.OneToOneField(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="subscription",
    )

    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name="subscriptions",
    )

    status = models.CharField(
        max_length=20,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.ACTIVE,
    )

    stripe_customer_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    stripe_subscription_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    current_period_start = models.DateTimeField(
        null=True,
        blank=True,
    )

    current_period_end = models.DateTimeField(
        null=True,
        blank=True,
    )

    cancel_at_period_end = models.BooleanField(default=False)

    class Meta:
        db_table = "billing_subscriptions"
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["stripe_customer_id"]),
            models.Index(fields=["stripe_subscription_id"]),
        ]

    def __str__(self):
        return f"{self.organization} - {self.plan}"


class PaymentEvent(UUIDModel, TimeStampedModel):
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="payment_events",
    )

    event_type = models.CharField(max_length=255)

    stripe_event_id = models.CharField(
        max_length=255,
        unique=True,
    )

    payload = models.JSONField()

    processed = models.BooleanField(default=False)

    class Meta:
        db_table = "billing_payment_events"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["stripe_event_id"]),
            models.Index(fields=["event_type"]),
            models.Index(fields=["processed"]),
        ]

    def __str__(self):
        return self.stripe_event_id
