from rest_framework import serializers


class HealthCheckSerializer(serializers.Serializer):
    status = serializers.CharField()
    service = serializers.CharField()
    database = serializers.CharField(required=False)
    redis = serializers.CharField(required=False)
    version = serializers.CharField(required=False)
