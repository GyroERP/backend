"""Base serializers for GyroERP apps to extend."""

from rest_framework import serializers

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


class KernelSerializer(serializers.ModelSerializer):
    """
    Base serializer for GyroERP business models.

    Adds read-only audit fields (created_at, updated_at, created_by username).
    Business app serializers should inherit this and declare their Meta.
    """

    created_at = serializers.ReadOnlyField()
    updated_at = serializers.ReadOnlyField()
    created_by_username = serializers.SerializerMethodField()

    def get_created_by_username(self, obj) -> str | None:
        created_by = getattr(obj, "created_by", None)
        return created_by.username if created_by else None


# ---------------------------------------------------------------------------
# Phase 1
# ---------------------------------------------------------------------------

class CompanySerializer(serializers.ModelSerializer):
    is_subsidiary = serializers.ReadOnlyField()

    class Meta:
        model = Company
        fields = [
            "id", "name", "code",
            "country", "state", "currency", "language",
            "timezone", "street", "street2", "city", "zip_code",
            "email", "phone", "vat",
            "parent", "logo_url", "website",
            "is_active", "is_subsidiary",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class InstalledAppSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstalledApp
        fields = [
            "id", "app_label", "gyro_name", "version", "state",
            "depends", "category", "description", "created_at",
        ]
        read_only_fields = ["id", "state", "created_at"]


class SystemParameterSerializer(serializers.ModelSerializer):
    value = serializers.SerializerMethodField()

    class Meta:
        model = SystemParameter
        fields = ["id", "key", "value", "description", "is_secret", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_value(self, obj) -> str:
        return "***" if obj.is_secret else obj.value

    def to_internal_value(self, data):
        internal = super().to_internal_value(data)
        if "value" in data:
            internal["value"] = data["value"]
        return internal


class AuditLogSerializer(serializers.ModelSerializer):
    user_display = serializers.StringRelatedField(source="user")
    company_display = serializers.StringRelatedField(source="company")

    class Meta:
        model = AuditLog
        fields = [
            "id", "timestamp", "action", "user_display", "company_display",
            "object_repr", "changes", "ip_address", "request_id", "extra",
        ]
        read_only_fields = fields


# ---------------------------------------------------------------------------
# Phase 2
# ---------------------------------------------------------------------------

class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = [
            "id", "iso_code", "name", "symbol", "symbol_position",
            "decimal_places", "rounding", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class CurrencyRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CurrencyRate
        fields = ["id", "currency", "company", "rate", "date", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class LanguageSerializer(serializers.ModelSerializer):
    is_rtl = serializers.ReadOnlyField()

    class Meta:
        model = Language
        fields = [
            "id", "code", "name", "iso_code", "url_code", "direction", "is_rtl",
            "date_format", "time_format", "decimal_point", "thousands_separator",
            "week_start", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = [
            "id", "code", "name", "alpha3", "numeric_code", "phone_code",
            "address_format", "zip_required", "state_required", "vat_label",
            "currency", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class CountryStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CountryState
        fields = ["id", "country", "name", "code", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class SequenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sequence
        fields = [
            "id", "name", "code", "prefix", "suffix", "padding", "step",
            "implementation", "use_date_range", "next_number",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class PartnerTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnerTag
        fields = ["id", "name", "color", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class PartnerSerializer(serializers.ModelSerializer):
    commercial_partner_id = serializers.SerializerMethodField()
    display_name = serializers.ReadOnlyField()
    depth = serializers.ReadOnlyField()

    class Meta:
        model = Partner
        fields = [
            "id", "name", "display_name", "partner_type", "is_company",
            "company", "parent", "address_type",
            "ref", "vat", "email", "phone", "mobile", "website",
            "street", "street2", "city", "zip_code",
            "state", "country", "language", "timezone",
            "tags", "notes",
            "is_active", "depth", "path", "commercial_partner_id",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "path", "depth", "display_name", "created_at", "updated_at"]

    def get_commercial_partner_id(self, obj) -> str | None:
        cp = obj.commercial_partner
        return str(cp.pk) if cp else None


class RecordRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecordRule
        fields = [
            "id", "name", "model_name", "groups", "domain",
            "can_read", "can_write", "can_create", "can_delete",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = [
            "id", "name", "content_type", "object_id",
            "file", "file_size", "checksum", "mime_type", "is_public",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "file_size", "checksum", "created_at", "updated_at"]


# ---------------------------------------------------------------------------
# Phase 3
# ---------------------------------------------------------------------------

class ModelPermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelPermission
        fields = [
            "id", "model_name", "group",
            "can_read", "can_write", "can_create", "can_delete",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class GroupExtensionSerializer(serializers.ModelSerializer):
    group_name = serializers.StringRelatedField(source="group")

    class Meta:
        model = GroupExtension
        fields = [
            "id", "group", "group_name", "implied_groups",
            "category", "sequence", "max_key_duration_days",
            "is_disjoint_with", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class APIKeySerializer(serializers.ModelSerializer):
    """List/detail serializer — never exposes the raw key."""
    is_expired = serializers.ReadOnlyField()

    class Meta:
        model = APIKey
        fields = [
            "id", "name", "prefix", "scope", "allowed_models",
            "ip_allowlist", "expires_at", "last_used_at", "last_used_ip",
            "request_count", "is_active", "is_expired",
            "deactivated_at", "deactivated_reason",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "prefix", "last_used_at", "last_used_ip", "request_count",
            "is_expired", "deactivated_at", "created_at", "updated_at",
        ]


class APIKeyGenerateSerializer(serializers.Serializer):
    """Write serializer for key creation — returns the one-time raw key."""
    name = serializers.CharField(max_length=200)
    scope = serializers.ChoiceField(choices=["full", "read", "write", "custom"], default="full")
    allowed_models = serializers.ListField(child=serializers.CharField(), default=list)
    ip_allowlist = serializers.ListField(child=serializers.CharField(), default=list)
    expires_at = serializers.DateTimeField(required=False, allow_null=True)


class MailServerSerializer(serializers.ModelSerializer):
    class Meta:
        model = MailServer
        fields = [
            "id", "name", "company", "smtp_host", "smtp_port", "smtp_encryption",
            "smtp_user", "from_filter", "sequence", "debug_mode",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class FieldDefaultSerializer(serializers.ModelSerializer):
    value = serializers.SerializerMethodField()

    class Meta:
        model = FieldDefault
        fields = [
            "id", "model_name", "field_name", "user", "company", "value",
            "json_value", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_value(self, obj):
        return obj.value


class SavedFilterSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedFilter
        fields = [
            "id", "name", "model_name", "domain", "context", "sort",
            "user", "company", "is_default", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class LoginLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoginLog
        fields = [
            "id", "user", "username_attempted", "event",
            "timestamp", "ip_address", "user_agent", "api_key",
        ]
        read_only_fields = fields


class UserPreferencesSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPreferences
        fields = [
            "id", "user",
            "language", "timezone", "date_format", "time_format",
            "decimal_point", "thousands_sep", "currency",
            "default_company",
            "notify_email", "notify_inapp", "email_digest",
            "notify_on_mention", "notify_on_assign",
            "notify_on_activity", "notify_on_approval",
            "theme", "display_density", "records_per_page",
            "show_tutorials", "keyboard_shortcuts",
            "accessibility_high_contrast", "font_size",
            "email_signature", "out_of_office",
            "out_of_office_message", "out_of_office_until",
            "two_factor_enabled", "session_timeout_minutes",
            "data", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "user", "created_at", "updated_at"]


class BankSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bank
        fields = ["id", "name", "bic", "country", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class PartnerBankSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnerBank
        fields = [
            "id", "partner", "bank", "acc_number", "acc_type",
            "currency", "is_primary", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class DecimalPrecisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DecimalPrecision
        fields = ["id", "name", "company", "digits", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
