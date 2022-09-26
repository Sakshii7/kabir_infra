from django.http import JsonResponse


def get_response(message="", status_code=200):
    return {
        "result": message,
        "status_code": status_code,
    }


class ExceptionMiddleware(object):
    def __init__(self, exc_get_response):
        self.get_response = exc_get_response

    def __call__(self, request):

        response = self.get_response(request)

        if response.status_code == 500:
            response = get_response(
                message="Internal server error",
                status_code=response.status_code
            )
            return JsonResponse(response, status=response['status_code'])

        if response.status_code == 400:
            response = get_response(
                message="Page not found, invalid url",
                status_code=response.status_code
            )
            return JsonResponse(response, status=response['status_code'])

        return response
