from apps.organizations.constants import OrganizationRole
from apps.organizations.selectors.membership_selector import get_membership


def can_manage_members(
    *,
    user,
    organization,
):
    membership = get_membership(
        user=user,
        organization=organization,
    )

    if not membership:
        return False

    return membership.role in [
        OrganizationRole.OWNER,
        OrganizationRole.ADMIN,
    ]
