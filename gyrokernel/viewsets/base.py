"""Base viewsets for GyroERP apps to extend."""

from io import StringIO

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from gyrokernel.models import (
    Attachment,
    AuditLog,
    Company,
    Country,
    CountryState,
    Currency,
    CurrencyRate,
    InstalledApp,
    Language,
    Partner,
    PartnerTag,
    RecordRule,
    Sequence,
    SystemParameter,
)
from gyrokernel.serializers.base import (
    AttachmentSerializer,
    AuditLogSerializer,
    CompanySerializer,
    CountrySerializer,
    CountryStateSerializer,
    CurrencyRateSerializer,
    CurrencySerializer,
    InstalledAppSerializer,
    LanguageSerializer,
    PartnerSerializer,
    PartnerTagSerializer,
    RecordRuleSerializer,
    SequenceSerializer,
    SystemParameterSerializer,
)


class KernelModelViewSet(ModelViewSet):
    """
    Base ModelViewSet for all GyroERP business resources.

    Provides: DjangoFilterBackend, SearchFilter, OrderingFilter,
    and automatic created_by / updated_by injection from the request user.
    Business app viewsets should inherit this.
    """

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    pagination_class = PageNumberPagination

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(created_by=user, updated_by=user)

    def perform_update(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(updated_by=user)


# ---------------------------------------------------------------------------
# Phase 1 viewsets
# ---------------------------------------------------------------------------

class CompanyViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    queryset = Company.objects.filter(is_active=True)
    serializer_class = CompanySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["is_active", "country", "currency"]
    search_fields = ["name", "code", "email", "vat"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]


class InstalledAppViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, GenericViewSet):
    queryset = InstalledApp.objects.all()
    serializer_class = InstalledAppSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["state", "category"]
    search_fields = ["gyro_name", "app_label"]

    @action(detail=False, methods=["post"], url_path=r"(?P<app_label>[^/.]+)/install")
    def install(self, request, app_label=None):
        from django.core.management import call_command

        out = StringIO()
        try:
            call_command("gyro_install_app", app_label, stdout=out)
            return Response({"detail": out.getvalue().strip()})
        except Exception as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"], url_path=r"(?P<app_label>[^/.]+)/uninstall")
    def uninstall(self, request, app_label=None):
        from django.core.management import call_command

        out = StringIO()
        try:
            call_command("gyro_uninstall_app", app_label, stdout=out)
            return Response({"detail": out.getvalue().strip()})
        except Exception as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


class SystemParameterViewSet(ModelViewSet):
    queryset = SystemParameter.objects.all()
    serializer_class = SystemParameterSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["is_secret"]
    search_fields = ["key", "description"]
    ordering = ["key"]


class AuditLogViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, GenericViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["action", "company"]
    search_fields = ["object_repr", "request_id", "ip_address"]
    ordering_fields = ["timestamp"]
    ordering = ["-timestamp"]


# ---------------------------------------------------------------------------
# Phase 2 viewsets
# ---------------------------------------------------------------------------

class CurrencyViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    queryset = Currency.objects.all()
    serializer_class = CurrencySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["is_active"]
    search_fields = ["iso_code", "name", "symbol"]
    ordering_fields = ["iso_code", "name"]
    ordering = ["iso_code"]


class CurrencyRateViewSet(ModelViewSet):
    queryset = CurrencyRate.objects.select_related("currency", "company").all()
    serializer_class = CurrencyRateSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["currency", "company"]
    ordering_fields = ["date"]
    ordering = ["-date"]


class LanguageViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    queryset = Language.objects.all()
    serializer_class = LanguageSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["is_active", "direction"]
    search_fields = ["code", "name", "iso_code"]
    ordering_fields = ["name", "code"]
    ordering = ["name"]


class CountryViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    queryset = Country.objects.select_related("currency").all()
    serializer_class = CountrySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["is_active", "currency"]
    search_fields = ["code", "name", "alpha3"]
    ordering_fields = ["name", "code"]
    ordering = ["name"]


class CountryStateViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    queryset = CountryState.objects.select_related("country").all()
    serializer_class = CountryStateSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["country"]
    search_fields = ["name", "code"]
    ordering_fields = ["name", "code"]
    ordering = ["name"]


class SequenceViewSet(ModelViewSet):
    queryset = Sequence.objects.all()
    serializer_class = SequenceSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["is_active", "implementation", "use_date_range"]
    search_fields = ["code", "name"]
    ordering_fields = ["code", "name"]
    ordering = ["code"]

    @action(detail=False, methods=["post"], url_path=r"(?P<code>[^/.]+)/next")
    def next_value(self, request, code=None):
        """Return the next formatted sequence value without requiring the PK."""
        from datetime import date

        date_str = request.data.get("date")
        use_date = None
        if date_str:
            try:
                use_date = date.fromisoformat(date_str)
            except ValueError:
                return Response(
                    {"detail": "Invalid date format. Use YYYY-MM-DD."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        try:
            value = Sequence.next_by_code(code, date=use_date)
            return Response({"value": value})
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)


class PartnerTagViewSet(ModelViewSet):
    queryset = PartnerTag.objects.all()
    serializer_class = PartnerTagSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name"]
    ordering = ["name"]


class PartnerViewSet(ModelViewSet):
    queryset = Partner.objects.select_related("country", "state", "language", "company").all()
    serializer_class = PartnerSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["partner_type", "is_company", "is_active", "country", "company"]
    search_fields = ["name", "email", "phone", "vat", "ref"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]


class RecordRuleViewSet(ModelViewSet):
    queryset = RecordRule.objects.all()
    serializer_class = RecordRuleSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["is_active", "model_name"]
    search_fields = ["name", "model_name"]
    ordering = ["model_name", "name"]


class AttachmentViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet,
):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["is_public", "content_type", "object_id"]
    search_fields = ["name", "checksum", "mime_type"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]
