import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestLogin:
    @pytest.fixture
    def url(self):
        return reverse("accounts:login")

    def test_login_success(self, api_client, user, url):
        response = api_client.post(
            url,
            {
                "email": user.email,
                "password": "password123",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data

    def test_wrong_password(self, api_client, user, url):
        response = api_client.post(
            url,
            {
                "email": user.email,
                "password": "wrongpassword",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_unknown_email(self, api_client, url):
        response = api_client.post(
            url,
            {
                "email": "unknown@example.com",
                "password": "password123",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_inactive_user(self, api_client, user, url):
        user.is_active = False
        user.save()

        response = api_client.post(
            url,
            {
                "email": user.email,
                "password": "password123",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
