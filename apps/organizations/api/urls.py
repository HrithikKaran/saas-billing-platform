from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.organizations.api.views import (
    AcceptInvitationAPIView,
    OrganizationAddMemberAPIView,
    OrganizationInviteAPIView,
    OrganizationMembersAPIView,
    OrganizationViewSet,
)

router = DefaultRouter()

router.register(
    "",
    OrganizationViewSet,
    basename="organizations",
)


urlpatterns = [
    path(
        "",
        include(router.urls),
    ),
    path(
        "<uuid:organization_id>/members/",
        OrganizationMembersAPIView.as_view(),
        name="organization-members",
    ),
    path(
        "<uuid:organization_id>/members/add/",
        OrganizationAddMemberAPIView.as_view(),
        name="organization-add-member",
    ),
    path(
        "<uuid:organization_id>/invite/",
        OrganizationInviteAPIView.as_view(),
        name="organization-invite",
    ),
    path(
        "invitations/<uuid:token>/accept/",
        AcceptInvitationAPIView.as_view(),
        name="accept-invitation",
    ),
]
