from rest_framework import status
from rest_framework.exceptions import APIException


class ApplicationException(Exception):
    """
    Base application exception.
    """

    status_code = status.HTTP_400_BAD_REQUEST
    default_message = "Application Error"

    def __init__(self, message=None):
        self.message = message or self.default_message
        super().__init__(self.message)


class UserNotFoundException(ApplicationException):
    status_code = status.HTTP_404_NOT_FOUND
    default_message = "User does not exist."


class DuplicateMembershipException(ApplicationException):
    status_code = status.HTTP_409_CONFLICT
    default_message = "User is already a member of this organization."


class InvitationExpiredException(ApplicationException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_message = "Invitation has expired."


class InvitationAlreadyAcceptedException(ApplicationException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_message = "Invitation has already been accepted."


class InvitationEmailMisMatchException(ApplicationException):
    status_code = status.HTTP_403_FORBIDDEN
    default_message = "You cannot accept an invitation sent to another email."


class OrganizationAccessDeniedException(ApplicationException):
    status_code = status.HTTP_403_FORBIDDEN
    default_message = "You don't have access to this organization."


class StripeCustomerNotFoundException(ApplicationException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_message = "Stripe customer does not exist."


class PlanNotLinkedToStripeException(ApplicationException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_message = "Plan is not linked to Stripe."


class CheckoutSessionCreationException(ApplicationException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_message = "Unable to create Stripe checkout session."


class PlanNotFoundException(ApplicationException):
    status_code = status.HTTP_404_NOT_FOUND
    default_message = "Request plan does not exist."


class NoActiveSubscriptionException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = (
        "This organization has no active paid subscription to modify. "
        "Use the checkout flow to start a new subscription."
    )
    default_code = "no_active_subscription"


class SubscriptionAlreadyOnPlanException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "The organization's subscription is already on this plan."
    default_code = "subscription_already_on_plan"


class SubscriptionAlreadyCanceledException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = (
        "The subscription is already scheduled for cancellation "
        "(or has no pending cancellation to reactivate)."
    )
    default_code = "subscription_already_canceled"


# new for billing portal


# NEW
class BillingPortalException(APIException):
    status_code = status.HTTP_502_BAD_GATEWAY
    default_detail = (
        "Failed to create a billing portal session. " "Please try again in a moment."
    )
    default_code = "billing_portal_error"
