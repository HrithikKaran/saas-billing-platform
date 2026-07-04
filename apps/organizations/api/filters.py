import django_filters

from apps.organizations.models import Organization


class OrganizationFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        field_name="name",
        lookup_expr="icontains",
    )

    slug = django_filters.CharFilter(
        field_name="slug",
        lookup_expr="icontains",
    )

    class Meta:
        model = Organization

        fields = [
            "name",
            "slug",
        ]
