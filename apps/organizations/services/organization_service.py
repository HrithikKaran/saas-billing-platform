from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from apps.billing.services.billing_service import assign_free_subscription
from apps.common.exceptions.exceptions import (
    DuplicateMembershipException,
    UserNotFoundException,
)
from apps.notifications.tasks import send_invitation_email
from apps.organizations.constants import InvitationStatus, OrganizationRole
from apps.organizations.models import Membership, Organization, OrganizationInvitation

User = get_user_model()


@transaction.atomic
def create_organization(
    *,
    user,
    name: str,
):
    slug = slugify(name)

    organization = Organization.objects.create(
        name=name,
        slug=slug,
        owner=user,
    )

    Membership.objects.create(
        organization=organization,
        user=user,
        role=OrganizationRole.OWNER,
    )
    assign_free_subscription(organization=organization)

    return organization


def add_member(
    *,
    organization,
    email: str,
    role: str,
):
    user = User.objects.filter(
        email=email,
    ).first()

    if user is None:
        raise UserNotFoundException

    if Membership.objects.filter(
        organization=organization,
        user=user,
    ).exists():
        raise DuplicateMembershipException()

    membership = Membership.objects.create(
        organization=organization,
        user=user,
        role=role,
    )

    return membership


def create_invitation(
    *,
    organization,
    invited_by,
    email,
    role,
):
    invitation = OrganizationInvitation.objects.create(
        organization=organization,
        email=email,
        role=role,
        invited_by=invited_by,
        expires_at=timezone.now() + timedelta(days=7),
    )

    send_invitation_email.delay(
        invitation.email,
        str(invitation.token),
    )

    return invitation


def accept_invitation(
    *,
    invitation,
    user,
):
    if invitation.status != InvitationStatus.PENDING:
        raise ValueError("Invitation already used.")

    if invitation.expires_at < timezone.now():
        raise ValueError("Invitation expired.")

    if invitation.email.lower() != user.email.lower():
        raise ValueError("Invitation email mismatch.")

    membership = Membership.objects.create(
        organization=invitation.organization,
        user=user,
        role=invitation.role,
    )

    invitation.status = InvitationStatus.ACCEPTED

    invitation.save(update_fields=["status"])

    return membership
