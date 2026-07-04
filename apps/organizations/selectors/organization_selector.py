from django.shortcuts import get_object_or_404

from apps.organizations.models import Organization


def get_user_organizations(user):
    return (
        Organization.objects.filter(memberships__user=user)
        .select_related("owner")
        .distinct()
    )


def get_user_organization_by_id(
    *,
    user,
    organization_id,
):
    queryset = (
        Organization.objects.filter(memberships__user=user)
        .select_related("owner")
        .distinct()
    )

    return get_object_or_404(
        queryset,
        id=organization_id,
    )
