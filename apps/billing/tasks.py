# apps/billing/tasks.py
#
# Celery tasks for async billing side-effects.
# Autodiscovered by Celery because config/celery.py uses app.autodiscover_tasks().
#
# To run the worker locally during development:
#   celery -A config worker --loglevel=info
#
# In production, this same worker command runs as a separate process/container
# alongside Django. Tasks are enqueued by billing service functions and
# executed asynchronously by the worker — Django itself never blocks on them.

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


# NEW: async email notification for invoice.payment_failed.
#
# Using @shared_task rather than @app.task keeps this file decoupled from
# the Celery app instance in config/celery.py — it binds at runtime, which
# means this module can be imported without a live Celery app (e.g. in tests
# or during Django startup before Celery is initialized).
#
# bind=True gives us access to `self` for retry logic. max_retries=3 means
# Celery will retry up to 3 times if an exception escapes the task body,
# with exponential backoff via self.retry(countdown=...).
@shared_task(bind=True, max_retries=3)
def send_payment_failed_email(
    self, organization_id: str, organization_name: str, customer_email: str
):
    """
    Sends a "payment failed" notification email to the organization's billing
    contact. Called asynchronously by handle_invoice_payment_failed() in the
    webhook handler after the subscription is marked PAST_DUE.

    Currently logs to the console — swap the logger.info() call for a real
    email send (django.core.mail.send_mail, SendGrid, Mailgun, etc.) when
    you have an email provider configured.

    Args:
        organization_id:    UUID string of the local Organization.
        organization_name:  Human-readable org name for the email body.
        customer_email:     The billing contact's email address (pulled from
                            the Stripe invoice in the webhook handler).

    Retry behaviour:
        If the task raises an exception (e.g. SMTP timeout), Celery retries
        it automatically up to max_retries times with a 60-second countdown
        between attempts. After max_retries exhaustion, the exception
        propagates and the task moves to the FAILED state.
    """
    try:
        logger.info(
            "========== PAYMENT FAILED EMAIL ==========\n"
            "To:           %s\n"
            "Organization: %s (id: %s)\n"
            "Subject:      Action required: Your payment failed\n"
            "Body:         Your recent payment failed. Please update your\n"
            "              payment method to avoid losing access to your plan.\n"
            "              Visit your billing portal to update your card.",
            customer_email,
            organization_name,
            organization_id,
        )

        # ----------------------------------------------------------------
        # TODO: replace the log above with a real email send, e.g.:
        #
        # from django.core.mail import send_mail
        # send_mail(
        #     subject="Action required: Your payment failed",
        #     message=(
        #         f"Hi {organization_name},\n\n"
        #         "Your recent payment failed and your account has been moved "
        #         "to past-due status.\n\n"
        #         "Please update your payment method to restore full access:\n"
        #         f"{settings.STRIPE_BILLING_PORTAL_RETURN_URL}\n\n"
        #         "If you have questions, reply to this email.\n\n"
        #         "— The Billing Team"
        #     ),
        #     from_email=settings.DEFAULT_FROM_EMAIL,
        #     recipient_list=[customer_email],
        #     fail_silently=False,  # let exceptions propagate so Celery retries
        # )
        # ----------------------------------------------------------------

        logger.info(
            "Payment failed notification logged for organization %s (%s).",
            organization_name,
            organization_id,
        )

    except Exception as exc:
        logger.error(
            "Failed to send payment failed email to %s (org %s): %s",
            customer_email,
            organization_id,
            exc,
            exc_info=True,
        )
        # Retry with exponential-ish backoff: 60s, 120s, 240s
        raise self.retry(exc=exc, countdown=60 * (2**self.request.retries))
