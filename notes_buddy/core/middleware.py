import uuid
import threading

_request_id = threading.local()

def get_request_id():
    return getattr(_request_id, "value", None)

class RequestIDMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _request_id.value = request.headers.get(
            "X-Request_ID", str(uuid.uuid4())
        )
        response = self.get_response(request)
        response["X-Request-ID"] = _request_id.value
        return response