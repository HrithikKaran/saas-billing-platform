from django.shortcuts import get_object_or_404

from apps.organizations.models import OrganizationInvitation


def get_invitation_by_token(
    token,
):
    return get_object_or_404(OrganizationInvitation, token=token)
