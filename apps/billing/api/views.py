# apps/billing/api/views.py
import logging

import stripe
from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.billing.api.serializers import BillingPortalResponseSerializer  # NEW
from apps.billing.api.serializers import BillingPortalSerializer  # NEW
from apps.billing.api.serializers import (
    CancelSubscriptionSerializer,
    ChangeSubscriptionPlanSerializer,
    CheckoutResponseSerializer,
    CheckoutSerializer,
    CreateCustomerResponseSerializer,
    CreateCustomerSerializer,
    PlanSerializer,
    SubscriptionActionResponseSerializer,
)
from apps.billing.models import Plan, Subscription
from apps.billing.selectors.plan_selector import get_active_plans
from apps.billing.services.billing_service import get_billing_portal_url  # NEW
from apps.billing.services.billing_service import (
    cancel_subscription,
    change_subscription_plan,
    create_checkout,
    create_stripe_customer,
    reactivate_canceled_subscription,
)
from apps.billing.webhooks.handlers import process_stripe_event
from apps.common.exceptions.exceptions import PlanNotFoundException
from apps.organizations.selectors.organization_selector import (
    get_user_organization_by_id,
)

logger = logging.getLogger(__name__)


class ListPlansAPIView(APIView):
    serializer_class = PlanSerializer

    def get(self, request, *args, **kwargs):
        plans = get_active_plans()
        serializer = PlanSerializer(plans, many=True)
        return Response(serializer.data)


class CreateStripeCustomerAPIView(APIView):
    serializer_class = CreateCustomerSerializer

    @extend_schema(
        request=CreateCustomerSerializer,
        responses=CreateCustomerResponseSerializer,
    )
    def post(self, request, *args, **kwargs):
        serializer = CreateCustomerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        organization_id = serializer.validated_data["organization_id"]

        organization = get_user_organization_by_id(
            user=request.user,
            organization_id=organization_id,
        )
        subscription = Subscription.objects.get(organization=organization)
        customer = create_stripe_customer(
            subscription=subscription,
            user=request.user,
        )

        return Response({"customer_id": customer.id}, status=status.HTTP_201_CREATED)


class CreateCheckoutAPIView(APIView):
    serializer_class = CheckoutSerializer

    @extend_schema(
        request=CheckoutSerializer,
        responses=CheckoutResponseSerializer,
    )
    def post(self, request, *args, **kwargs):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        organization = get_user_organization_by_id(
            user=request.user,
            organization_id=serializer.validated_data["organization_id"],
        )
        subscription = Subscription.objects.get(organization=organization)

        try:
            plan = Plan.objects.get(
                id=serializer.validated_data["plan_id"],
                is_active=True,
            )
        except Plan.DoesNotExist as err:
            raise PlanNotFoundException() from err

        session = create_checkout(subscription=subscription, plan=plan)
        return Response({"checkout_url": session.url}, status=status.HTTP_200_OK)


class ChangeSubscriptionPlanAPIView(APIView):
    serializer_class = ChangeSubscriptionPlanSerializer

    @extend_schema(
        request=ChangeSubscriptionPlanSerializer,
        responses=SubscriptionActionResponseSerializer,
    )
    def post(self, request, *args, **kwargs):
        serializer = ChangeSubscriptionPlanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        organization = get_user_organization_by_id(
            user=request.user,
            organization_id=serializer.validated_data["organization_id"],
        )

        subscription = change_subscription_plan(
            organization=organization,
            new_plan_id=str(serializer.validated_data["plan_id"]),
        )

        # Returns OLD plan state — DB updates asynchronously via webhook.
        return Response(
            {
                "organization_id": organization.id,
                "plan_id": subscription.plan.id,
                "plan_name": subscription.plan.name,
                "status": subscription.status,
                "cancel_at_period_end": subscription.cancel_at_period_end,
                "detail": (
                    "Plan change requested. It will be confirmed shortly "
                    "once Stripe processes the billing update."
                ),
            },
            status=status.HTTP_202_ACCEPTED,
        )


class CancelSubscriptionAPIView(APIView):
    serializer_class = CancelSubscriptionSerializer

    @extend_schema(
        request=CancelSubscriptionSerializer,
        responses=SubscriptionActionResponseSerializer,
    )
    def post(self, request, *args, **kwargs):
        serializer = CancelSubscriptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        organization = get_user_organization_by_id(
            user=request.user,
            organization_id=serializer.validated_data["organization_id"],
        )
        subscription = cancel_subscription(organization=organization)

        return Response(
            {
                "organization_id": organization.id,
                "plan_id": subscription.plan.id,
                "plan_name": subscription.plan.name,
                "status": subscription.status,
                "cancel_at_period_end": subscription.cancel_at_period_end,
                "detail": (
                    "Cancellation scheduled. Access continues until the "
                    "end of the current billing period."
                ),
            },
            status=status.HTTP_202_ACCEPTED,
        )


class ReactivateSubscriptionAPIView(APIView):
    serializer_class = CancelSubscriptionSerializer

    @extend_schema(
        request=CancelSubscriptionSerializer,
        responses=SubscriptionActionResponseSerializer,
    )
    def post(self, request, *args, **kwargs):
        serializer = CancelSubscriptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        organization = get_user_organization_by_id(
            user=request.user,
            organization_id=serializer.validated_data["organization_id"],
        )
        subscription = reactivate_canceled_subscription(organization=organization)

        return Response(
            {
                "organization_id": organization.id,
                "plan_id": subscription.plan.id,
                "plan_name": subscription.plan.name,
                "status": subscription.status,
                "cancel_at_period_end": subscription.cancel_at_period_end,
                "detail": "Cancellation reversed. Subscription will continue to renew.",
            },
            status=status.HTTP_202_ACCEPTED,
        )


# NEW: Billing Portal view.
#
# Returns a short-lived Stripe-hosted URL. The frontend should redirect the
# user to it immediately — the URL expires after a short period (minutes).
#
# No webhook handling is needed for portal-initiated changes: the portal
# fires the same customer.subscription.updated / customer.subscription.deleted
# events your existing handlers already process. The only thing this endpoint
# does is create the session so the user can access the portal.
class BillingPortalAPIView(APIView):
    serializer_class = BillingPortalSerializer

    @extend_schema(
        request=BillingPortalSerializer,
        responses=BillingPortalResponseSerializer,
    )
    def post(self, request, *args, **kwargs):
        serializer = BillingPortalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        organization = get_user_organization_by_id(
            user=request.user,
            organization_id=serializer.validated_data["organization_id"],
        )

        portal_url = get_billing_portal_url(organization=organization)

        return Response(
            {"url": portal_url},
            status=status.HTTP_200_OK,
        )


class StripeWebhookAPIView(APIView):
    authentication_classes = []
    permission_classes = []
    serializer_class = None

    @extend_schema(exclude=True)
    def post(self, request):
        logger.info("Stripe webhook received.")
        payload = request.body
        signature = request.META.get("HTTP_STRIPE_SIGNATURE")

        logger.debug("Payload length: %s", len(payload))

        try:
            event = stripe.Webhook.construct_event(
                payload=payload,
                sig_header=signature,
                secret=settings.STRIPE_WEBHOOK_SECRET,
            )
        except ValueError:
            return Response(
                {"detail": "Invalid payload"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except stripe.error.SignatureVerificationError:
            return Response(
                {"detail": "Invalid signature"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        logger.info("Stripe event type: %s", event["type"])

        try:
            process_stripe_event(event)
        except Exception:
            import traceback

            traceback.print_exc()
            raise

        return Response(status=status.HTTP_200_OK)
