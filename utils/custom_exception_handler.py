from django.http import JsonResponse
from kabir_infra_app import settings


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
        return response

    @staticmethod
    def process_exception(request, exception):
        if settings.DEBUG:
            if exception:
                msg = f'{exception.__class__.__name__}: {exception}'
                print(msg)
                response = get_response(
                    result="Bad request",
                    status_code=400
                )
                return JsonResponse(response, status=response['status_code'])
