# #apps/billing/api/serialziers.py
# from rest_framework import serializers
# from apps.billing.models import Plan


# class CheckoutSerializer(
#     serializers.Serializer
# ):
#     organization_id = (
#         serializers.UUIDField()
#     )
#     plan_id = serializers.UUIDField()


# class PlanSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Plan
#         fields = (
#             "id",
#             "name",
#             "description",
#             "price",
#             "max_users",
#             "api_limit",
#         )


# class CreateCustomerSerializer(serializers.Serializer):
#     organization_id = serializers.UUIDField()


# class CreateCustomerResponseSerializer(serializers.Serializer):
#     customer_id = serializers.CharField()


# class CheckoutResponseSerializer(serializers.Serializer):
#     checkout_url = serializers.URLField()


# # NEW: serializers for upgrade/downgrade, cancel, and reactivate endpoints.

# class ChangeSubscriptionPlanSerializer(serializers.Serializer):
#     """
#     Used for both upgrade and downgrade — same request shape, since the
#     direction is inferred server-side from current vs. new plan price.
#     """
#     organization_id = serializers.UUIDField()
#     plan_id = serializers.UUIDField(
#         help_text="The new plan to switch to. Must differ from the current plan."
#     )


# class CancelSubscriptionSerializer(serializers.Serializer):
#     organization_id = serializers.UUIDField()


# class SubscriptionActionResponseSerializer(serializers.Serializer):
#     """
#     Generic response for change-plan/cancel/reactivate actions. Intentionally
#     returns the current known DB state immediately so the frontend has
#     something to show right away — but note current_period_start/end,
#     cancel_at_period_end, and plan may not reflect the Stripe change yet
#     (proration/webhook timing — see docstrings in billing_service.py).
#     """
#     organization_id = serializers.UUIDField()
#     plan_id = serializers.UUIDField()
#     plan_name = serializers.CharField()
#     status = serializers.CharField()
#     cancel_at_period_end = serializers.BooleanField()
#     detail = serializers.CharField()


# above code is working fine.
# below code include new endpoint for billing portal


# apps/billing/api/serializers.py
from rest_framework import serializers

from apps.billing.models import Plan


class CheckoutSerializer(serializers.Serializer):
    organization_id = serializers.UUIDField()
    plan_id = serializers.UUIDField()


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = (
            "id",
            "name",
            "description",
            "price",
            "max_users",
            "api_limit",
        )


class CreateCustomerSerializer(serializers.Serializer):
    organization_id = serializers.UUIDField()


class CreateCustomerResponseSerializer(serializers.Serializer):
    customer_id = serializers.CharField()


class CheckoutResponseSerializer(serializers.Serializer):
    checkout_url = serializers.URLField()


class ChangeSubscriptionPlanSerializer(serializers.Serializer):
    organization_id = serializers.UUIDField()
    plan_id = serializers.UUIDField(
        help_text="The new plan to switch to. Must differ from the current plan."
    )


class CancelSubscriptionSerializer(serializers.Serializer):
    organization_id = serializers.UUIDField()


class SubscriptionActionResponseSerializer(serializers.Serializer):
    organization_id = serializers.UUIDField()
    plan_id = serializers.UUIDField()
    plan_name = serializers.CharField()
    status = serializers.CharField()
    cancel_at_period_end = serializers.BooleanField()
    detail = serializers.CharField()


# NEW: Billing Portal serializers.
# The request is just organization_id (same as Cancel).
# The response is the short-lived portal URL — the frontend should redirect
# the user to this URL immediately; it expires after a short time.


class BillingPortalSerializer(serializers.Serializer):
    organization_id = serializers.UUIDField()


class BillingPortalResponseSerializer(serializers.Serializer):
    url = serializers.URLField(
        help_text=(
            "Short-lived Stripe Billing Portal URL. Redirect the user here "
            "immediately — the URL expires after a short period."
        )
    )
