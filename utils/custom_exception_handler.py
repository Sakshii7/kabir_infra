from rest_framework import status
from django.http import JsonResponse


def get_response(result="", status_code=200):
    return {
        "result": result,
        "status_code": status_code,
    }


class ExceptionMiddleware(object):
    def __init__(self, exc_get_response):
        self.get_response = exc_get_response

    def __call__(self, request):

        response = self.get_response(request)

        if response.status_code != 200:
            response = get_response(
                result="Bad request",
                status_code=400
            )
            return JsonResponse(response, status=status.HTTP_400_BAD_REQUEST)

        return response
