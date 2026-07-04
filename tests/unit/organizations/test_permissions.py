from apps.organizations.constants import OrganizationRole
from apps.organizations.permissions.role_permissions import can_assign_role


def test_owner_can_assign_admin():
    assert can_assign_role(
        actor_role=OrganizationRole.OWNER,
        target_role=OrganizationRole.ADMIN,
    )


def test_admin_cannot_assign_admin():
    assert not can_assign_role(
        actor_role=OrganizationRole.ADMIN,
        target_role=OrganizationRole.ADMIN,
    )


def test_admin_can_assign_member():
    assert can_assign_role(
        actor_role=OrganizationRole.ADMIN,
        target_role=OrganizationRole.MEMBER,
    )
