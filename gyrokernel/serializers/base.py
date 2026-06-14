"""Base serializers for GyroERP apps to extend."""

from rest_framework import serializers

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
