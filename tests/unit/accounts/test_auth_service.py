import pytest

from apps.accounts.services.auth_service import create_user


@pytest.mark.django_db
def test_create_user():
    user = create_user(
        email="john@example.com", username="john", password="password123"
    )

    assert user.email == "john@example.com"
    assert user.check_password("password123")
