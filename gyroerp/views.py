"""Project-level views."""

from django.http import JsonResponse


def health_check(_request):
    """Lightweight health endpoint for load balancers and monitoring."""
    return JsonResponse(
        {
            "status": "ok",
            "service": "gyroerp-backend",
        }
    )
