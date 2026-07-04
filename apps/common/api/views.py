from django.db import connections
from django.db.utils import OperationalError
from django_redis import get_redis_connection
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.api.serializers import HealthCheckSerializer


class HealthCheckAPIView(APIView):
    permission_classes = []
    serializer_class = HealthCheckSerializer

    def get(self, request):
        # -- Check database connection
        db_status = "unknown"
        try:
            db_conn = connections["default"]
            db_conn.cursor()
            db_status = "connected"
        except OperationalError:
            db_status = "unhealthy"

        # redis health check
        redis_status = "unknown"
        try:
            redis_conn = get_redis_connection("default")
            redis_conn.ping()
            redis_status = "connected"
        except Exception:
            redis_status = "unhealthy"

        overall_status = (
            "healthy"
            if db_status == "connected" and redis_status == "connected"
            else "degraded"
        )

        return Response(
            {
                "status": overall_status,
                "service": "saas-billing-platform",
                "database": db_status,
                "redis": redis_status,
                "version": "1.0.0",
            }
        )
