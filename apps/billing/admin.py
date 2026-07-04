from django.contrib import admin

from .models import PaymentEvent, Plan, Subscription


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "price",
        "max_users",
        "api_limit",
        "stripe_price_id",
        "is_active",
    )

    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "organization",
        "plan",
        "status",
        "current_period_end",
        "cancel_at_period_end",
        "stripe_customer_id",
        "stripe_subscription_id",
        "current_period_start",
    )

    list_filter = ("status",)
    search_fields = (
        "organization__name",
        "stripe_customer_id",
        "stripe_subscription_id",
    )


@admin.register(PaymentEvent)
class PaymentEventAdmin(admin.ModelAdmin):
    list_display = (
        "stripe_event_id",
        "event_type",
        "organization",
        "processed",
        "created_at",
    )

    list_filter = (
        "processed",
        "event_type",
    )

    search_fields = (
        "stripe_event_id",
        "event_type",
    )
