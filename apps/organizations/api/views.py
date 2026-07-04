from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema
from rest_framework import generics, status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.common.pagination import DefaultPagination
from apps.organizations.api.filters import OrganizationFilter
from apps.organizations.api.serializers import (
    AcceptInvitationSerializer,
    AddMemberSerializer,
    CreateInvitationSerializer,
    InvitationSerializer,
    MembershipSerializer,
    OrganizationCreateSerializer,
    OrganizationSerializer,
)
from apps.organizations.models import Membership, Organization
from apps.organizations.permissions.organization_permissions import can_manage_members
from apps.organizations.permissions.role_permissions import can_assign_role
from apps.organizations.selectors.invitation_selector import get_invitation_by_token
from apps.organizations.selectors.membership_selector import (
    get_membership_by_user_and_organization,
)
from apps.organizations.selectors.organization_selector import (
    get_user_organization_by_id,
    get_user_organizations,
)
from apps.organizations.services.organization_service import (
    accept_invitation,
    add_member,
    create_invitation,
    create_organization,
)


class OrganizationViewSet(
    viewsets.GenericViewSet,
):
    """
    Phase 9.2

    Migrated endpoints:

    GET     /organizations/
    POST    /organizations/
    GET     /organizations/{id}/
    """

    serializer_class = OrganizationSerializer

    filter_backends = [
        DjangoFilterBackend,
    ]

    filterset_class = OrganizationFilter

    pagination_class = DefaultPagination

    def get_queryset(self):
        # called by drf_spectacular to generate schema for list endpoint
        if getattr(self, "swagger_fake_view", False):
            return Organization.objects.none()
        return get_user_organizations(self.request.user)

    def list(
        self,
        request,
    ):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = OrganizationSerializer(
                page,
                many=True,
            )

            return self.get_paginated_response(serializer.data)

        serializer = OrganizationSerializer(
            queryset,
            many=True,
        )

        return Response(serializer.data)

    def create(
        self,
        request,
    ):
        serializer = OrganizationCreateSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        organization = create_organization(
            user=request.user,
            name=serializer.validated_data["name"],
        )

        return Response(
            OrganizationSerializer(organization).data,
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="id",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description="Organization UUID",
            )
        ]
    )
    def retrieve(
        self,
        request,
        pk=None,
    ):
        organization = get_user_organization_by_id(
            user=request.user,
            organization_id=pk,
        )

        return Response(OrganizationSerializer(organization).data)


class OrganizationMembersAPIView(generics.ListAPIView):
    serializer_class = MembershipSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Membership.objects.none()
        organization = get_user_organization_by_id(
            user=self.request.user,
            organization_id=self.kwargs["organization_id"],
        )

        return organization.memberships.select_related("user")


class OrganizationAddMemberAPIView(generics.GenericAPIView):
    serializer_class = AddMemberSerializer

    def post(
        self,
        request,
        *args,
        **kwargs,
    ):
        organization = get_user_organization_by_id(
            user=request.user,
            organization_id=kwargs["organization_id"],
        )

        if not can_manage_members(
            user=request.user,
            organization=organization,
        ):
            raise PermissionDenied("You do not have permission " "to add members.")

        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        requested_role = serializer.validated_data["role"]

        membership = get_membership_by_user_and_organization(
            user=request.user,
            organization=organization,
        )

        if not can_assign_role(
            actor_role=membership.role,
            target_role=requested_role,
        ):
            raise PermissionDenied("You cannot assign this role.")

        new_membership = add_member(
            organization=organization,
            email=serializer.validated_data["email"],
            role=requested_role,
        )

        return Response(
            MembershipSerializer(new_membership).data,
            status=status.HTTP_201_CREATED,
        )


class OrganizationInviteAPIView(generics.GenericAPIView):
    serializer_class = CreateInvitationSerializer

    def post(
        self,
        request,
        *args,
        **kwargs,
    ):
        organization = get_user_organization_by_id(
            user=request.user,
            organization_id=kwargs["organization_id"],
        )

        if not can_manage_members(
            user=request.user,
            organization=organization,
        ):
            raise PermissionDenied("You cannot invite users.")

        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        invitation = create_invitation(
            organization=organization,
            invited_by=request.user,
            email=serializer.validated_data["email"],
            role=serializer.validated_data["role"],
        )

        return Response(
            InvitationSerializer(invitation).data,
            status=status.HTTP_201_CREATED,
        )


class AcceptInvitationAPIView(generics.GenericAPIView):
    serializer_class = AcceptInvitationSerializer

    def post(
        self,
        request,
        token,
    ):
        invitation = get_invitation_by_token(token)

        membership = accept_invitation(
            invitation=invitation,
            user=request.user,
        )

        return Response(MembershipSerializer(membership).data)
