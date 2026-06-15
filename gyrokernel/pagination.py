"""Default pagination class for all GyroERP API endpoints."""

from rest_framework.pagination import PageNumberPagination


class GyroPageNumberPagination(PageNumberPagination):
    """
    Bounded page-number pagination.

    Enforces max_page_size=200 to prevent DoS via ?page_size=9999999.
    ISO 27001 A.13.1.1 — network controls must prevent resource exhaustion.
    """

    page_size = 25
    max_page_size = 200
    page_size_query_param = "page_size"
