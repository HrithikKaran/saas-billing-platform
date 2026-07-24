import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestCurrentUser:
    @pytest.fixture
    def url(self):
        return reverse("accounts:me")

    def test_authenticate_user(self, authenticated_client, user, url):
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == user.email

    def test_anonymous_user(self, api_client, url):
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
