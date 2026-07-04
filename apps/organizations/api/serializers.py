from rest_framework import serializers

from apps.organizations.constants import OrganizationRole
from apps.organizations.models import Membership, Organization, OrganizationInvitation


class OrganizationCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization

        fields = (
            "id",
            "name",
            "slug",
            "owner",
            "created_at",
        )


class MembershipSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        source="user.email",
        read_only=True,
    )

    class Meta:
        model = Membership

        fields = (
            "id",
            "email",
            "role",
            "created_at",
        )


class AddMemberSerializer(serializers.Serializer):
    email = serializers.EmailField()

    role = serializers.ChoiceField(choices=OrganizationRole.choices)


class CreateInvitationSerializer(serializers.Serializer):
    email = serializers.EmailField()

    role = serializers.ChoiceField(choices=OrganizationRole.choices)


class InvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationInvitation

        fields = (
            "id",
            "email",
            "role",
            "status",
            "token",
            "expires_at",
        )


class AcceptInvitationSerializer(serializers.Serializer):
    pass
