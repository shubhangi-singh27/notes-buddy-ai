import uuid
import threading
import time
import logging

logger = logging.getLogger(__name__)

_request_id = threading.local()

REQUEST_LOG_EXCLUDE = [
    ("/api/health", "GET"),
    ("/api/documents", "GET"),
]

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

class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.startswith("/api/"):
            return self.get_response(request)

        path_normalized = request.path.rstrip("/") or "/"

        if any(
            path_normalized == p.rstrip("/") and request.method == m
            for p, m in REQUEST_LOG_EXCLUDE
        ):
            return self.get_response(request)

        start = time.time()
        response = self.get_response(request)
        duration_ms = round((time.time() - start) * 1000)

        user_obj = getattr(request, "user", None)
        if user_obj and getattr(user_obj,"is_authenticated", False):
            user = getattr(user_obj, "username", "anonymous")
        else:
            user = "anonymous"

        logger.info(
            f"{request.method} {request.path} {response.status_code} "
            f"{duration_ms}ms user={user}"
        )

        return response