# apps/billing/clients/stripe_client.py
import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_customer(
    *,
    email: str,
    organization_name: str,
):
    customer = stripe.Customer.create(
        email=email,
        name=organization_name,
        metadata={
            "organization": organization_name,
        },
    )

    return customer


def create_checkout_session(
    *,
    customer_id: str,
    price_id: str,
    organization_id: str,
    plan_id: str,
    success_url: str,
    cancel_url: str,
):
    session = stripe.checkout.Session.create(
        customer=customer_id,
        payment_method_types=["card"],
        mode="subscription",
        line_items=[
            {
                "price": price_id,
                "quantity": 1,
            }
        ],
        metadata={"organization_id": organization_id, "plan_id": plan_id},
        success_url=success_url,
        cancel_url=cancel_url,
    )

    return session


def get_subscription_item_id(*, stripe_subscription_id: str) -> str:
    """
    Returns the id of the first (and, in this app, only) subscription item
    on a subscription. Needed because changing a subscription's price is
    done by updating the *item*, not the subscription itself.
    """
    stripe_sub = stripe.Subscription.retrieve(
        stripe_subscription_id,
        expand=["items"],
    )
    items = stripe_sub["items"]["data"]

    if not items:
        raise ValueError(f"Stripe subscription {stripe_subscription_id} has no items.")

    return items[0]["id"]


def change_subscription_price(
    *,
    stripe_subscription_id: str,
    new_price_id: str,
):
    """
    Swaps the price on an existing subscription (used for both upgrade and
    downgrade). proration_behavior="always_invoice" charges/credits the
    prorated difference immediately.
    """
    item_id = get_subscription_item_id(stripe_subscription_id=stripe_subscription_id)

    updated_subscription = stripe.Subscription.modify(
        stripe_subscription_id,
        items=[
            {
                "id": item_id,
                "price": new_price_id,
            }
        ],
        proration_behavior="always_invoice",
    )

    return updated_subscription


def cancel_subscription_at_period_end(*, stripe_subscription_id: str):
    """
    Marks the subscription to cancel at the end of the current paid period.
    """
    updated_subscription = stripe.Subscription.modify(
        stripe_subscription_id,
        cancel_at_period_end=True,
    )

    return updated_subscription


def reactivate_subscription(*, stripe_subscription_id: str):
    """
    Undoes a pending cancellation (cancel_at_period_end=True -> False).
    """
    updated_subscription = stripe.Subscription.modify(
        stripe_subscription_id,
        cancel_at_period_end=False,
    )

    return updated_subscription


# NEW: Billing Portal session creation.
#
# Prerequisites (must be done once in the Stripe Dashboard before this works):
#   Test mode → Billing → Customer portal → configure features → Save
# Without that step, this call will raise:
#   stripe.error.InvalidRequestError: No default configuration exists for
#   customer portal sessions...
#
# The portal gives customers a Stripe-hosted UI to:
#   - Update payment methods
#   - Download invoices
#   - View billing history
#   - Update billing details (name, address, email)
#   - Manage or cancel subscriptions (if enabled in portal config)
#
# Any subscription changes made through the portal fire the same
# customer.subscription.updated / customer.subscription.deleted webhooks
# that your existing handlers already process — no extra webhook handling
# needed specifically for portal actions.
def create_billing_portal_session(
    *,
    customer_id: str,
    return_url: str,
):
    """
    Creates a short-lived Stripe Billing Portal session URL for a customer.

    Args:
        customer_id:  The Stripe customer ID (e.g. "cus_xxx") stored on the
                      organization's Subscription row.
        return_url:   Where Stripe redirects the customer after they leave
                      the portal (e.g. your app's dashboard or settings page).
                      Must be a fully-qualified URL.

    Returns:
        A Stripe BillingPortal.Session object. The .url attribute is the
        short-lived URL to redirect the customer to.
    """
    session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=return_url,
    )

    return session
