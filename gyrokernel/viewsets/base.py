"""Base viewsets for GyroERP apps to extend."""

from io import StringIO

from django.db import models

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from gyrokernel.models import (
    APIKey,
    Attachment,
    AuditLog,
    Bank,
    Company,
    Country,
    CountryState,
    Currency,
    CurrencyRate,
    DecimalPrecision,
    FieldDefault,
    GroupExtension,
    InstalledApp,
    Language,
    LoginLog,
    MailServer,
    ModelPermission,
    Partner,
    PartnerBank,
    PartnerTag,
    RecordRule,
    SavedFilter,
    Sequence,
    SystemParameter,
    UserPreferences,
)
from gyrokernel.serializers.base import (
    APIKeyGenerateSerializer,
    APIKeySerializer,
    AttachmentSerializer,
    AuditLogSerializer,
    BankSerializer,
    CompanySerializer,
    CountrySerializer,
    CountryStateSerializer,
    CurrencyRateSerializer,
    CurrencySerializer,
    DecimalPrecisionSerializer,
    FieldDefaultSerializer,
    GroupExtensionSerializer,
    InstalledAppSerializer,
    LanguageSerializer,
    LoginLogSerializer,
    MailServerSerializer,
    ModelPermissionSerializer,
    PartnerBankSerializer,
    PartnerSerializer,
    PartnerTagSerializer,
    RecordRuleSerializer,
    SavedFilterSerializer,
    SequenceSerializer,
    SystemParameterSerializer,
    UserPreferencesSerializer,
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


# ---------------------------------------------------------------------------
# Phase 3 viewsets
# ---------------------------------------------------------------------------

class ModelPermissionViewSet(ModelViewSet):
    queryset = ModelPermission.objects.select_related("group").all()
    serializer_class = ModelPermissionSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["is_active", "model_name", "group"]
    search_fields = ["model_name", "group__name"]
    ordering = ["model_name"]


class GroupExtensionViewSet(ModelViewSet):
    queryset = GroupExtension.objects.select_related("group").prefetch_related("implied_groups").all()
    serializer_class = GroupExtensionSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["category"]
    search_fields = ["group__name", "category"]
    ordering = ["category", "sequence"]


class APIKeyViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet,
):
    """
    API Key management.

    List/Retrieve/Delete only — creation goes through the `generate` action
    which returns the one-time raw key.  Update is intentionally unsupported
    (revoke + regenerate instead).
    """

    serializer_class = APIKeySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["scope", "is_active"]
    search_fields = ["name", "prefix"]
    ordering = ["-created_at"]
    gyro_skip_permission = True  # auth endpoint, skip model-level checks

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return APIKey.objects.all()
        return APIKey.objects.filter(user=user)

    @action(detail=False, methods=["post"], url_path="generate")
    def generate(self, request):
        """Create a new API key and return the one-time raw key."""
        serializer = APIKeyGenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            instance, raw_key = APIKey.generate(
                user=request.user,
                name=data["name"],
                scope=data.get("scope", "full"),
                allowed_models=data.get("allowed_models", []),
                ip_allowlist=data.get("ip_allowlist", []),
                expires_at=data.get("expires_at"),
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "id": str(instance.pk),
                "prefix": instance.prefix,
                "raw_key": raw_key,
                "warning": "Store this key securely. It cannot be retrieved again.",
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="deactivate")
    def deactivate(self, request, pk=None):
        """Deactivate (revoke) an API key."""
        api_key = self.get_object()
        reason = request.data.get("reason", "")
        api_key.deactivate(reason=reason)
        return Response({"detail": "API key deactivated."})


class MailServerViewSet(ModelViewSet):
    queryset = MailServer.objects.select_related("company").all()
    serializer_class = MailServerSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["is_active", "smtp_encryption", "company"]
    search_fields = ["name", "smtp_host"]
    ordering = ["sequence", "name"]

    @action(detail=True, methods=["post"], url_path="test")
    def test_connection(self, request, pk=None):
        """Send a test email to verify SMTP configuration."""
        import smtplib
        from email.message import EmailMessage

        server = self.get_object()
        to_address = request.data.get("to", request.user.email)
        if not to_address:
            return Response({"detail": "Provide a 'to' email address."}, status=status.HTTP_400_BAD_REQUEST)

        msg = EmailMessage()
        msg["Subject"] = "GyroERP SMTP Test"
        msg["From"] = request.data.get("from", server.smtp_user or "noreply@gyroerp.local")
        msg["To"] = to_address
        msg.set_content("This is a test message from GyroERP. SMTP configuration is working.")

        try:
            server.send(msg)
            return Response({"detail": f"Test email sent to {to_address}."})
        except smtplib.SMTPException as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)


class FieldDefaultViewSet(ModelViewSet):
    queryset = FieldDefault.objects.all()
    serializer_class = FieldDefaultSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["model_name", "user", "company"]
    search_fields = ["model_name", "field_name"]
    ordering = ["model_name", "field_name"]


class SavedFilterViewSet(ModelViewSet):
    queryset = SavedFilter.objects.all()
    serializer_class = SavedFilterSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["model_name", "user", "company", "is_default"]
    search_fields = ["name", "model_name"]
    ordering = ["model_name", "name"]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return SavedFilter.objects.all()
        # Users see their own filters and shared (user=None) filters
        return SavedFilter.objects.filter(
            models.Q(user=user) | models.Q(user__isnull=True)
        )


class LoginLogViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, GenericViewSet):
    queryset = LoginLog.objects.select_related("user", "api_key").all()
    serializer_class = LoginLogSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["event", "user"]
    search_fields = ["username_attempted", "ip_address", "user__username"]
    ordering = ["-timestamp"]
    gyro_skip_permission = True


class UserPreferencesViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    GenericViewSet,
):
    serializer_class = UserPreferencesSerializer
    gyro_skip_permission = True

    def get_queryset(self):
        return UserPreferences.objects.filter(user=self.request.user)

    @action(detail=False, methods=["get", "put", "patch"], url_path="me")
    def me(self, request):
        """Get or update the current user's preferences (create on first access)."""
        prefs, _ = UserPreferences.objects.get_or_create(
            user=request.user,
            defaults={"timezone": getattr(request.user, "timezone", "UTC")},
        )
        if request.method == "GET":
            return Response(UserPreferencesSerializer(prefs).data)
        partial = request.method == "PATCH"
        serializer = UserPreferencesSerializer(prefs, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class BankViewSet(ModelViewSet):
    queryset = Bank.objects.select_related("country").all()
    serializer_class = BankSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["is_active", "country"]
    search_fields = ["name", "bic"]
    ordering = ["name"]


class PartnerBankViewSet(ModelViewSet):
    queryset = PartnerBank.objects.select_related("partner", "bank", "currency").all()
    serializer_class = PartnerBankSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["partner", "acc_type", "is_primary"]
    search_fields = ["acc_number", "partner__name", "bank__name"]
    ordering = ["-is_primary", "acc_number"]


class DecimalPrecisionViewSet(ModelViewSet):
    queryset = DecimalPrecision.objects.select_related("company").all()
    serializer_class = DecimalPrecisionSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["company"]
    search_fields = ["name"]
    ordering = ["name"]
