import uuid

from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel, UUIDModel
from apps.organizations.constants import InvitationStatus, OrganizationRole


class Organization(UUIDModel, TimeStampedModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_organizations",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class Membership(UUIDModel, TimeStampedModel):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="memberships",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships"
    )
    role = models.CharField(
        max_length=20, choices=OrganizationRole.choices, default=OrganizationRole.MEMBER
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "organization",
                    "user",
                ],
                name="unique_organization_user",
            ),
        ]
        indexes = [
            models.Index(
                fields=["organization"],
            ),
            models.Index(
                fields=["user"],
            ),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} -" f"{self.organization.name}"


class OrganizationInvitation(
    UUIDModel,
    TimeStampedModel,
):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="invitations",
    )

    email = models.EmailField()

    role = models.CharField(
        max_length=20,
        choices=OrganizationRole.choices,
    )

    token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
    )

    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_invitations",
    )

    status = models.CharField(
        max_length=20,
        choices=InvitationStatus.choices,
        default=InvitationStatus.PENDING,
    )

    expires_at = models.DateTimeField()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.email} - " f"{self.organization.name}"
