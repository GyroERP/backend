"""Request ID middleware — attaches a unique ID to every request and response."""

import uuid


class RequestIDMiddleware:
    """
    Attaches an X-Request-ID header to every HTTP request and response.

    If the incoming request already carries the header (set by a load balancer
    or API gateway), that value is reused to preserve cross-service traceability.
    The ID is also stored on request.request_id for use in views and AuditLog.
    """

    INBOUND_HEADER = "HTTP_X_REQUEST_ID"
    OUTBOUND_HEADER = "X-Request-ID"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.META.get(self.INBOUND_HEADER) or str(uuid.uuid4())
        request.request_id = request_id

        response = self.get_response(request)
        response[self.OUTBOUND_HEADER] = request_id
        return response
