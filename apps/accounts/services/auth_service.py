from django.contrib.auth import get_user_model

User = get_user_model()


def create_user(**validated_data):
    password = validated_data.pop("password")

    user = User.objects.create_user(password=password, **validated_data)
    return user
