from django.shortcuts import get_object_or_404

from apps.organizations.models import Membership


def get_membership(
    *,
    user,
    organization,
):
    return Membership.objects.filter(
        user=user,
        organization=organization,
    ).first()


def get_membership_by_user_and_organization(
    *,
    user,
    organization,
):
    return get_object_or_404(
        Membership,
        user=user,
        organization=organization,
    )
