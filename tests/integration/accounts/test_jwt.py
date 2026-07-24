import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken


@pytest.mark.django_db
class TestJWT:
    @pytest.fixture
    def url(self):
        return reverse("token_refresh")

    def test_refresh_token_success(self, api_client, user, url):
        refresh = RefreshToken.for_user(user)

        response = api_client.post(
            url,
            {
                "refresh": str(refresh),
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data

    def test_invalid_refresh_token(self, api_client, url):
        response = api_client.post(
            url,
            {
                "refresh": "invalid-token",
            },
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
