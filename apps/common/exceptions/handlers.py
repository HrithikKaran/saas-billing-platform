from rest_framework.response import Response
from rest_framework.views import exception_handler

from apps.common.exceptions.exceptions import ApplicationException


def custom_exception_handler(exc, context):
    if isinstance(exc, ApplicationException):
        return Response(
            {
                "success": False,
                "message": exc.message,
                "data": None,
            },
            status=exc.status_code,
        )

    response = exception_handler(exc, context)

    if response is not None:
        response.data = {
            "success": False,
            "message": "Request failed.",
            "errors": response.data,
        }

    return response
