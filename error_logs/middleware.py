"""Middleware that stores the current request so the logging handler can access it."""
from .handlers import set_current_request, clear_current_request


class ErrorLogMiddleware:
    """Makes the current request available to the DatabaseLogHandler."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        set_current_request(request)
        try:
            response = self.get_response(request)
            return response
        finally:
            clear_current_request()
