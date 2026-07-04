from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.api.serializers import HealthCheckSerializer


class HealthCheckAPIView(APIView):
    permission_classes = []
    serializer_class = HealthCheckSerializer

    def get(self, request):
        return Response(
            {
                "status": "healthy",
                "service": "saas-billing-platform",
            }
        )
