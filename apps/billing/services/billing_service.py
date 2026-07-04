# apps/billing/services/billing_service.py
import json
import logging
from datetime import UTC, datetime

import stripe
from django.conf import settings
from django.db import transaction

from apps.billing.clients.stripe_client import create_billing_portal_session  # NEW
from apps.billing.clients.stripe_client import (
    cancel_subscription_at_period_end,
    change_subscription_price,
    create_checkout_session,
    create_customer,
    reactivate_subscription,
)
from apps.billing.constants import PlanType, SubscriptionStatus
from apps.billing.models import Plan, Subscription
from apps.common.exceptions.exceptions import (
    BillingPortalException,  # NEW — add to exceptions.py (see exceptions_additions.py)
)
from apps.common.exceptions.exceptions import (
    CheckoutSessionCreationException,
    NoActiveSubscriptionException,
    PlanNotFoundException,
    PlanNotLinkedToStripeException,
    StripeCustomerNotFoundException,
    SubscriptionAlreadyCanceledException,
    SubscriptionAlreadyOnPlanException,
)

logger = logging.getLogger(__name__)


STRIPE_STATUS_MAPPING = {
    "active": SubscriptionStatus.ACTIVE,
    "trialing": SubscriptionStatus.TRIALING,
    "past_due": SubscriptionStatus.PAST_DUE,
    "canceled": SubscriptionStatus.CANCELED,
    "unpaid": SubscriptionStatus.UNPAID,
}


def stripe_timestamp_to_datetime(timestamp):
    if not timestamp:
        return None
    return datetime.fromtimestamp(timestamp, tz=UTC)


def stripe_object_to_dict(stripe_obj):
    """
    Converts a Stripe StripeObject to a plain Python dict so we can use
    normal dict operations (.get(), ["key"], etc.) everywhere downstream.
    If the input is already a plain dict (e.g. in tests), it passes through.
    """
    if hasattr(stripe_obj, "to_dict"):
        return stripe_obj.to_dict()
    return stripe_obj


def get_subscription_period(sub_dict):
    """
    Returns (current_period_start, current_period_end) as raw Unix timestamps
    (or None, None) from the first subscription item.
    Stripe moved these off the top-level Subscription object (API 2025-03-31+).
    """
    items = sub_dict.get("items", {}).get("data", [])

    if not items:
        logger.warning(
            "Stripe subscription %s has no items; cannot determine billing period.",
            sub_dict.get("id", "<unknown>"),
        )
        return None, None

    first_item = items[0]
    return first_item.get("current_period_start"), first_item.get("current_period_end")


def get_subscription_price_id(sub_dict):
    """
    Returns the Stripe price ID of the first subscription item, or None.
    """
    items = sub_dict.get("items", {}).get("data", [])
    if not items:
        return None
    price = items[0].get("price")
    if not price:
        return None
    return price.get("id")


def assign_free_subscription(*, organization):
    free_plan = Plan.objects.get(name=PlanType.FREE)
    subscription = Subscription.objects.create(
        organization=organization,
        plan=free_plan,
        status=SubscriptionStatus.ACTIVE,
    )
    return subscription


def create_stripe_customer(*, subscription, user):
    customer = create_customer(
        email=user.email,
        organization_name=subscription.organization.name,
    )
    subscription.stripe_customer_id = customer.id
    subscription.save(update_fields=["stripe_customer_id"])
    return customer


def create_checkout(*, subscription, plan):
    if not subscription.stripe_customer_id:
        raise StripeCustomerNotFoundException()

    if not plan.stripe_price_id:
        raise PlanNotLinkedToStripeException()

    try:
        session = create_checkout_session(
            customer_id=subscription.stripe_customer_id,
            price_id=plan.stripe_price_id,
            organization_id=str(subscription.organization.id),
            plan_id=str(plan.id),
            success_url=settings.STRIPE_SUCCESS_URL,
            cancel_url=settings.STRIPE_CANCEL_URL,
        )
        return session
    except Exception as err:
        raise CheckoutSessionCreationException() from err


def complete_subscription_checkout(
    *,
    organization,
    plan_id: str,
    stripe_subscription_id: str | None,
):
    try:
        subscription = Subscription.objects.select_related("plan", "organization").get(
            organization=organization
        )
    except Subscription.DoesNotExist:
        return

    try:
        plan = Plan.objects.get(id=plan_id, is_active=True)
    except Plan.DoesNotExist as err:
        raise PlanNotFoundException() from err

    subscription.plan = plan
    subscription.status = SubscriptionStatus.ACTIVE

    if stripe_subscription_id:
        subscription.stripe_subscription_id = stripe_subscription_id

        try:
            stripe_sub = stripe.Subscription.retrieve(
                stripe_subscription_id,
                expand=["items"],
            )
            logger.info(
                "========== STRIPE SUBSCRIPTION ==========\n%s",
                json.dumps(stripe_sub.to_dict(), indent=4, default=str),
            )
            sub_dict = stripe_object_to_dict(stripe_sub)
            period_start, period_end = get_subscription_period(sub_dict)
            subscription.current_period_start = stripe_timestamp_to_datetime(
                period_start
            )
            subscription.current_period_end = stripe_timestamp_to_datetime(period_end)
            subscription.cancel_at_period_end = sub_dict.get(
                "cancel_at_period_end", False
            )
        except Exception as e:
            logger.error(
                "Failed to retrieve subscription details from Stripe: %s",
                e,
                exc_info=True,
            )

    subscription.save(
        update_fields=[
            "plan",
            "status",
            "stripe_subscription_id",
            "current_period_start",
            "current_period_end",
            "cancel_at_period_end",
        ]
    )


def change_subscription_plan(*, organization, new_plan_id: str):
    """
    Upgrades or downgrades to a different paid plan. Payment is handled
    automatically by Stripe using the card on file — no new checkout URL.
    Stripe fires customer.subscription.updated to confirm the change.
    """
    try:
        subscription = Subscription.objects.select_related("plan", "organization").get(
            organization=organization
        )
    except Subscription.DoesNotExist as err:
        raise NoActiveSubscriptionException() from err

    if not subscription.stripe_subscription_id:
        raise NoActiveSubscriptionException()

    try:
        new_plan = Plan.objects.get(id=new_plan_id, is_active=True)
    except Plan.DoesNotExist as err:
        raise PlanNotFoundException() from err

    if not new_plan.stripe_price_id:
        raise PlanNotLinkedToStripeException()

    if subscription.plan_id == new_plan.id:
        raise SubscriptionAlreadyOnPlanException()

    logger.info(
        "Changing subscription %s for organization %s: %s -> %s.",
        subscription.stripe_subscription_id,
        organization.id,
        subscription.plan.name,
        new_plan.name,
    )

    change_subscription_price(
        stripe_subscription_id=subscription.stripe_subscription_id,
        new_price_id=new_plan.stripe_price_id,
    )

    return subscription


def cancel_subscription(*, organization):
    """Schedules cancellation at period end. Access continues until then."""
    try:
        subscription = Subscription.objects.select_related("plan", "organization").get(
            organization=organization
        )
    except Subscription.DoesNotExist as err:
        raise NoActiveSubscriptionException() from err

    if not subscription.stripe_subscription_id:
        raise NoActiveSubscriptionException()

    if subscription.cancel_at_period_end:
        raise SubscriptionAlreadyCanceledException()

    logger.info(
        "Scheduling cancellation at period end for subscription %s (organization %s).",
        subscription.stripe_subscription_id,
        organization.id,
    )

    cancel_subscription_at_period_end(
        stripe_subscription_id=subscription.stripe_subscription_id,
    )

    return subscription


def reactivate_canceled_subscription(*, organization):
    """Reverses a pending cancel_at_period_end=True."""
    try:
        subscription = Subscription.objects.select_related("plan", "organization").get(
            organization=organization
        )
    except Subscription.DoesNotExist as err:
        raise NoActiveSubscriptionException() from err

    if not subscription.stripe_subscription_id:
        raise NoActiveSubscriptionException()

    if not subscription.cancel_at_period_end:
        raise SubscriptionAlreadyCanceledException()

    logger.info(
        "Reactivating subscription %s (organization %s).",
        subscription.stripe_subscription_id,
        organization.id,
    )

    reactivate_subscription(
        stripe_subscription_id=subscription.stripe_subscription_id,
    )

    return subscription


def sync_subscription_from_stripe(*, stripe_subscription):
    """
    Syncs status, plan, billing period, and cancel flag from a Stripe
    subscription object. Converts StripeObject -> plain dict first so
    normal .get() calls work throughout.
    """
    sub_dict = stripe_object_to_dict(stripe_subscription)

    try:
        subscription = Subscription.objects.select_related(
            "organization",
            "plan",
        ).get(stripe_subscription_id=sub_dict["id"])
    except Subscription.DoesNotExist:
        logger.warning(
            "Stripe subscription %s not found locally.",
            sub_dict["id"],
        )
        return

    stripe_status = sub_dict["status"]
    status = STRIPE_STATUS_MAPPING.get(stripe_status, SubscriptionStatus.UNPAID)

    period_start, period_end = get_subscription_period(sub_dict)

    new_price_id = get_subscription_price_id(sub_dict)
    resolved_plan = None
    if new_price_id:
        try:
            resolved_plan = Plan.objects.get(
                stripe_price_id=new_price_id, is_active=True
            )
        except Plan.DoesNotExist:
            logger.warning(
                "Stripe subscription %s is on price %s which doesn't match "
                "any active local Plan. Plan field will NOT be updated.",
                sub_dict["id"],
                new_price_id,
            )

    with transaction.atomic():
        subscription.status = status

        if resolved_plan is not None and resolved_plan.id != subscription.plan_id:
            logger.info(
                "Subscription %s plan changed: %s -> %s.",
                subscription.id,
                subscription.plan.name,
                resolved_plan.name,
            )
            subscription.plan = resolved_plan

        subscription.current_period_start = stripe_timestamp_to_datetime(period_start)
        subscription.current_period_end = stripe_timestamp_to_datetime(period_end)
        subscription.cancel_at_period_end = sub_dict.get("cancel_at_period_end", False)

        subscription.save(
            update_fields=[
                "status",
                "plan",
                "current_period_start",
                "current_period_end",
                "cancel_at_period_end",
            ]
        )
        logger.info("Subscription %s synchronized successfully.", subscription.id)


def downgrade_to_free_on_cancellation(*, stripe_subscription):
    """
    Handles customer.subscription.deleted. Moves the org back to FREE
    rather than leaving them on a paid plan they're no longer paying for.
    """
    sub_dict = stripe_object_to_dict(stripe_subscription)

    try:
        subscription = Subscription.objects.select_related("organization", "plan").get(
            stripe_subscription_id=sub_dict["id"]
        )
    except Subscription.DoesNotExist:
        logger.warning(
            "Stripe subscription %s (deleted) not found locally.",
            sub_dict["id"],
        )
        return

    try:
        free_plan = Plan.objects.get(name=PlanType.FREE)
    except Plan.DoesNotExist:
        logger.error(
            "No FREE plan configured locally; cannot downgrade subscription %s.",
            subscription.id,
        )
        free_plan = None

    with transaction.atomic():
        subscription.status = SubscriptionStatus.CANCELED
        subscription.cancel_at_period_end = False

        if free_plan is not None:
            subscription.plan = free_plan

        subscription.save(update_fields=["status", "plan", "cancel_at_period_end"])

        logger.info(
            "Subscription %s for organization %s canceled; downgraded to FREE.",
            subscription.id,
            subscription.organization.id,
        )


def get_billing_portal_url(*, organization):
    """
    Creates a Stripe Billing Portal session and returns its short-lived URL.

    The portal lets the customer self-serve:
      - Update payment method (card)
      - Download past invoices / billing history
      - Update billing address, name, email
      - Manage or cancel their subscription (if enabled in portal config)

    Any subscription changes made in the portal trigger the same
    customer.subscription.updated / customer.subscription.deleted webhooks
    your existing handlers already process — no extra webhook code needed.

    One-time Stripe Dashboard setup required before this works:
      Test mode → Billing → Customer portal → configure features → Save
    """
    try:
        subscription = Subscription.objects.get(organization=organization)
    except Subscription.DoesNotExist as err:
        raise NoActiveSubscriptionException() from err

    if not subscription.stripe_customer_id:
        # No Stripe customer yet — org hasn't gone through checkout.
        raise NoActiveSubscriptionException()

    try:
        portal_session = create_billing_portal_session(
            customer_id=subscription.stripe_customer_id,
            # STRIPE_BILLING_PORTAL_RETURN_URL: where Stripe sends the customer
            # after they leave the portal. Add this to your settings.py, e.g.:
            #   STRIPE_BILLING_PORTAL_RETURN_URL = "http://localhost:3000/settings/billing"
            return_url=settings.STRIPE_BILLING_PORTAL_RETURN_URL,
        )
    except Exception as err:
        logger.error(
            "Failed to create billing portal session for organization %s: %s",
            organization.id,
            err,
            exc_info=True,
        )
        raise BillingPortalException() from err

    logger.info(
        "Billing portal session created for organization %s (customer %s).",
        organization.id,
        subscription.stripe_customer_id,
    )

    return portal_session.url


def handle_payment_failed(*, invoice_dict: dict):
    """
    Called when an invoice.payment_failed webhook arrives.

    Marks the subscription PAST_DUE synchronously, then enqueues a Celery
    task to send a payment-failed notification email asynchronously.

    Why async email?
      - Stripe expects a webhook response within 30 seconds or it retries.
      - Email sending (SMTP/API) can be slow or fail transiently.
      - Celery handles retry logic for the email independently of the
        webhook response, so a failed email send doesn't cause Stripe to
        re-deliver the entire webhook event.
    """
    # Local import to avoid circular import: tasks.py imports from billing_service
    # indirectly (via Django app infrastructure), so top-level import would fail.
    from apps.billing.tasks import send_payment_failed_email

    customer_id = invoice_dict.get("customer")
    # customer_email is on the invoice object in Stripe's API — it's the
    # email of the customer associated with the invoice.
    customer_email = invoice_dict.get("customer_email") or ""

    if not customer_id:
        logger.warning("invoice.payment_failed event missing customer ID; skipping.")
        return

    try:
        subscription = Subscription.objects.select_related("organization", "plan").get(
            stripe_customer_id=customer_id
        )
    except Subscription.DoesNotExist:
        logger.warning(
            "No local subscription found for Stripe customer %s on payment_failed.",
            customer_id,
        )
        return

    organization = subscription.organization

    # Update status synchronously — don't wait for customer.subscription.updated
    # (which Stripe also sends) to avoid a race between the two events.
    if subscription.status != SubscriptionStatus.PAST_DUE:
        subscription.status = SubscriptionStatus.PAST_DUE
        subscription.save(update_fields=["status"])
        logger.info(
            "Subscription %s for organization %s marked PAST_DUE after payment failure.",
            subscription.id,
            organization.id,
        )
    else:
        logger.info(
            "Subscription %s already PAST_DUE; skipping status update.",
            subscription.id,
        )

    # Enqueue email notification. .delay() is shorthand for .apply_async().
    # If no Celery worker is running, this silently queues to the broker.
    # Run `celery -A config worker --loglevel=info` to process it.
    send_payment_failed_email.delay(
        organization_id=str(organization.id),
        organization_name=organization.name,
        customer_email=customer_email,
    )

    logger.info(
        "Payment failed email task enqueued for organization %s.",
        organization.id,
    )
