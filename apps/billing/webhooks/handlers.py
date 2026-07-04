# apps/billing/webhooks/handlers.py

import json
import logging

from django.db import transaction

from apps.billing.models import PaymentEvent, Subscription
from apps.billing.services.billing_service import handle_payment_failed  # NEW
from apps.billing.services.billing_service import (
    complete_subscription_checkout,
    downgrade_to_free_on_cancellation,
    sync_subscription_from_stripe,
)
from apps.organizations.models import Organization

logger = logging.getLogger(__name__)


def process_stripe_event(event):

    logger.info(
        "========== FULL STRIPE WEBHOOK ==========\n%s",
        json.dumps(event.to_dict(), indent=4, default=str),
    )

    event_type = event["type"]

    logging.info("Processing Stripe event: %s", event_type)

    if event_type == "checkout.session.completed":
        handle_checkout_completed(event)

    elif event_type == "customer.subscription.updated":
        handle_subscription_update(event)

    elif event_type == "customer.subscription.deleted":
        handle_subscription_deleted(event)

    elif event_type == "invoice.payment_succeeded":
        handle_invoice_payment_succeeded(event)

    elif event_type == "invoice.payment_failed":  # NEW
        handle_invoice_payment_failed(event)

    else:
        logger.info("Ignoring Stripe event: %s", event_type)


def handle_checkout_completed(event):
    session = event["data"]["object"]
    event_id = event["id"]
    metadata = session["metadata"]
    organization_id = metadata["organization_id"]
    plan_id = metadata["plan_id"]

    if not organization_id or not plan_id:
        logger.warning("Checkout session metadata missing.")
        return

    try:
        organization = Organization.objects.get(id=organization_id)
    except Organization.DoesNotExist:
        logger.warning("Organization %s does not exist.", organization_id)
        return

    with transaction.atomic():
        payment_event, created = PaymentEvent.objects.get_or_create(
            stripe_event_id=event_id,
            defaults={
                "organization": organization,
                "event_type": event["type"],
                "payload": event.to_dict(),
                "processed": False,
            },
        )

        if not created and payment_event.processed:
            logger.info("Stripe event %s already processed.", event_id)
            return

        complete_subscription_checkout(
            organization=organization,
            plan_id=plan_id,
            stripe_subscription_id=session["subscription"],
        )

        payment_event.processed = True
        payment_event.save(update_fields=["processed"])
        logger.info("Checkout completed successfully.")


def handle_subscription_update(event):
    # Covers: upgrade, downgrade, cancel scheduled, reactivation —
    # all surface as customer.subscription.updated. sync_subscription_from_stripe
    # handles all four uniformly from the Stripe payload.
    stripe_subscription = event["data"]["object"]
    logger.info(
        "========== STRIPE SUBSCRIPTION PAYLOAD ==========\n%s",
        json.dumps(stripe_subscription.to_dict(), indent=4, default=str),
    )
    sync_subscription_from_stripe(stripe_subscription=stripe_subscription)


def handle_subscription_deleted(event):
    # Fires when cancel_at_period_end subscription actually expires, or on
    # immediate Dashboard cancellation. Downgrades org to FREE plan.
    stripe_subscription = event["data"]["object"]
    downgrade_to_free_on_cancellation(stripe_subscription=stripe_subscription)


def handle_invoice_payment_succeeded(event):
    invoice = event["data"]["object"]
    event_id = event["id"]
    customer_id = invoice["customer"]

    logger.info("Processing invoice.payment_succeeded: %s", event_id)

    try:
        subscription = Subscription.objects.select_related("organization").get(
            stripe_customer_id=customer_id
        )
        organization = subscription.organization
    except Subscription.DoesNotExist:
        logger.warning(
            "No local subscription found for Stripe customer %s", customer_id
        )
        return

    serialized_payload = json.loads(json.dumps(event.to_dict(), default=str))

    with transaction.atomic():
        payment_event, created = PaymentEvent.objects.get_or_create(
            stripe_event_id=event_id,
            defaults={
                "organization": organization,
                "event_type": event["type"],
                "payload": serialized_payload,
                "processed": True,
            },
        )
        if not created and payment_event.processed:
            logger.info("Invoice event %s already processed.", event_id)
            return

        logger.info("Invoice payment logged for Organization: %s", organization.id)


def handle_invoice_payment_failed(event):
    invoice = event["data"]["object"]
    event_id = event["id"]

    logger.info("Processing invoice.payment_failed: %s", event_id)

    # Convert StripeObject -> plain dict so .get() works safely downstream.
    invoice_dict = invoice.to_dict() if hasattr(invoice, "to_dict") else invoice

    # Delegate to the service layer (marks PAST_DUE + enqueues email task).
    handle_payment_failed(invoice_dict=invoice_dict)
