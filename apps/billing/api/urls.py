# apps/billing/api/urls.py
from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from apps.billing.api.views import BillingPortalAPIView  # NEW
from apps.billing.api.views import (
    CancelSubscriptionAPIView,
    ChangeSubscriptionPlanAPIView,
    CreateCheckoutAPIView,
    CreateStripeCustomerAPIView,
    ListPlansAPIView,
    ReactivateSubscriptionAPIView,
    StripeWebhookAPIView,
)

urlpatterns = [
    path(
        "plans/",
        ListPlansAPIView.as_view(),
        name="list-plans",
    ),
    path(
        "create-customer/",
        CreateStripeCustomerAPIView.as_view(),
        name="create-stripe-customer",
    ),
    path(
        "checkout/",
        CreateCheckoutAPIView.as_view(),
        name="stripe-checkout",
    ),
    path(
        "change-plan/",
        ChangeSubscriptionPlanAPIView.as_view(),
        name="change-subscription-plan",
    ),
    path(
        "cancel/",
        CancelSubscriptionAPIView.as_view(),
        name="cancel-subscription",
    ),
    path(
        "reactivate/",
        ReactivateSubscriptionAPIView.as_view(),
        name="reactivate-subscription",
    ),
    # NEW: Stripe Billing Portal — returns a short-lived URL the frontend
    # redirects the user to for self-serve payment/invoice management.
    path(
        "portal/",
        BillingPortalAPIView.as_view(),
        name="billing-portal",
    ),
    path(
        "webhooks/stripe/",
        csrf_exempt(StripeWebhookAPIView.as_view()),
        name="stripe-webhook",
    ),
]
