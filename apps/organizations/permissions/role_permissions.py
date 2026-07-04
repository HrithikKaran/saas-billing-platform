from apps.organizations.constants import OrganizationRole


def can_assign_role(
    *,
    actor_role,
    target_role,
):
    if actor_role == OrganizationRole.OWNER:
        return True

    if actor_role == OrganizationRole.ADMIN:
        return target_role == OrganizationRole.MEMBER

    return False
