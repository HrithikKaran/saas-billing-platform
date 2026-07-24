import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

User = get_user_model()


@pytest.mark.django_db
class TestUserRegistration:
    @pytest.fixture
    def url(self):
        return reverse("accounts:register")

    def test_register_user_success(self, api_client, url):
        payload = {
            "email": "john@example.com",
            "username": "john",
            "password": "password123",
            "first_name": "John",
            "last_name": "Doe",
        }

        response = api_client.post(url, payload)
        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.filter(email="john@example.com").exists()

    def test_duplicate_email(self, api_client, user, url):
        payload = {
            "email": user.email,
            "username": "anotheruser",
            "password": "password123",
        }

        response = api_client.post(url, payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data

    def test_duplicate_username(self, api_client, user, url):
        payload = {
            "email": "another@example.com",
            "username": user.username,
            "password": "password123",
        }

        response = api_client.post(url, payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "username" in response.data

    def test_weak_password(self, api_client, url):
        payload = {
            "email": "weak@example.com",
            "username": "weakuser",
            "password": "123",
        }

        response = api_client.post(url, payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "password" in response.data

    def test_missing_fields(self, api_client, url):
        response = api_client.post(url, {})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data
        assert "username" in response.data
        assert "password" in response.data
