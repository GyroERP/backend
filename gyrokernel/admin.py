"""Django admin configuration for GyroKernel models."""

from django.contrib import admin

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
    SequenceDateRange,
    SystemParameter,
    UserPreferences,
)


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "country", "currency", "is_active", "created_at"]
    list_filter = ["is_active", "country"]
    search_fields = ["name", "code", "email", "vat"]
    readonly_fields = ["id", "created_at", "updated_at"]
    autocomplete_fields = ["country", "state", "currency", "language"]


@admin.register(InstalledApp)
class InstalledAppAdmin(admin.ModelAdmin):
    list_display = ["gyro_name", "app_label", "version", "state", "category", "created_at"]
    list_filter = ["state", "category"]
    search_fields = ["gyro_name", "app_label"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(SystemParameter)
class SystemParameterAdmin(admin.ModelAdmin):
    list_display = ["key", "is_secret", "updated_at"]
    list_filter = ["is_secret"]
    search_fields = ["key", "description"]
    readonly_fields = ["id", "created_at", "updated_at"]

    def get_fields(self, request, obj=None):
        fields = list(super().get_fields(request, obj))
        if obj and obj.is_secret:
            fields = [f for f in fields if f != "value"]
        return fields


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["timestamp", "action", "user", "company", "object_repr", "ip_address"]
    list_filter = ["action", "company"]
    search_fields = ["object_repr", "request_id", "ip_address"]
    readonly_fields = [
        "id", "timestamp", "user", "company", "action",
        "content_type", "object_id", "object_repr", "changes",
        "ip_address", "request_id", "extra",
    ]
    date_hierarchy = "timestamp"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


# ---------------------------------------------------------------------------
# Phase 2 models
# ---------------------------------------------------------------------------

@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ["iso_code", "name", "symbol", "decimal_places", "is_active"]
    list_filter = ["is_active", "symbol_position"]
    search_fields = ["iso_code", "name"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(CurrencyRate)
class CurrencyRateAdmin(admin.ModelAdmin):
    list_display = ["currency", "rate", "date", "company"]
    list_filter = ["currency", "company"]
    search_fields = ["currency__iso_code"]
    readonly_fields = ["id", "created_at", "updated_at"]
    date_hierarchy = "date"


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "direction", "is_active"]
    list_filter = ["direction", "is_active"]
    search_fields = ["code", "name"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "alpha3", "currency", "is_active"]
    list_filter = ["is_active", "zip_required", "state_required"]
    search_fields = ["code", "name", "alpha3"]
    readonly_fields = ["id", "created_at", "updated_at"]
    autocomplete_fields = ["currency"]


@admin.register(CountryState)
class CountryStateAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "country"]
    list_filter = ["country"]
    search_fields = ["name", "code"]
    readonly_fields = ["id", "created_at", "updated_at"]
    autocomplete_fields = ["country"]


@admin.register(Sequence)
class SequenceAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "implementation", "use_date_range", "next_number", "is_active"]
    list_filter = ["implementation", "use_date_range", "is_active"]
    search_fields = ["code", "name"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(SequenceDateRange)
class SequenceDateRangeAdmin(admin.ModelAdmin):
    list_display = ["sequence", "date_from", "date_to", "next_number"]
    list_filter = ["sequence"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(PartnerTag)
class PartnerTagAdmin(admin.ModelAdmin):
    list_display = ["name", "color"]
    search_fields = ["name"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ["name", "partner_type", "is_company", "email", "phone", "country", "is_active"]
    list_filter = ["partner_type", "is_company", "is_active", "country"]
    search_fields = ["name", "email", "phone", "vat", "ref"]
    readonly_fields = ["id", "created_at", "updated_at"]
    autocomplete_fields = ["country", "state", "language", "company"]
    filter_horizontal = ["tags"]


@admin.register(RecordRule)
class RecordRuleAdmin(admin.ModelAdmin):
    list_display = ["name", "model_name", "is_active", "can_read", "can_write", "can_create", "can_delete"]
    list_filter = ["is_active", "model_name"]
    search_fields = ["name", "model_name"]
    readonly_fields = ["id", "created_at", "updated_at"]
    filter_horizontal = ["groups"]


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ["name", "mime_type", "file_size", "checksum", "is_public", "created_at"]
    list_filter = ["is_public", "mime_type"]
    search_fields = ["name", "checksum"]
    readonly_fields = ["id", "file_size", "checksum", "created_at", "updated_at"]


# ---------------------------------------------------------------------------
# Phase 3 models
# ---------------------------------------------------------------------------

@admin.register(ModelPermission)
class ModelPermissionAdmin(admin.ModelAdmin):
    list_display = ["model_name", "group", "can_read", "can_write", "can_create", "can_delete", "is_active"]
    list_filter = ["is_active", "can_read", "can_write", "can_create", "can_delete"]
    search_fields = ["model_name", "group__name"]
    readonly_fields = ["id", "created_at", "updated_at"]
    autocomplete_fields = ["group"]


@admin.register(GroupExtension)
class GroupExtensionAdmin(admin.ModelAdmin):
    list_display = ["group", "category", "sequence", "max_key_duration_days"]
    list_filter = ["category"]
    search_fields = ["group__name", "category"]
    readonly_fields = ["id", "created_at", "updated_at"]
    filter_horizontal = ["implied_groups", "is_disjoint_with"]
    autocomplete_fields = ["group"]


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ["name", "user", "prefix", "scope", "expires_at", "last_used_at", "is_active"]
    list_filter = ["scope", "is_active"]
    search_fields = ["name", "prefix", "user__username"]
    readonly_fields = [
        "id", "prefix", "hashed_key", "request_count",
        "last_used_at", "last_used_ip", "deactivated_at", "created_at", "updated_at",
    ]
    autocomplete_fields = ["user"]

    def has_add_permission(self, request):
        return False  # Keys must be created via APIKey.generate(), not admin


@admin.register(MailServer)
class MailServerAdmin(admin.ModelAdmin):
    list_display = ["name", "smtp_host", "smtp_port", "smtp_encryption", "company", "sequence", "is_active"]
    list_filter = ["smtp_encryption", "is_active", "debug_mode"]
    search_fields = ["name", "smtp_host", "smtp_user"]
    readonly_fields = ["id", "created_at", "updated_at"]
    autocomplete_fields = ["company"]


@admin.register(FieldDefault)
class FieldDefaultAdmin(admin.ModelAdmin):
    list_display = ["model_name", "field_name", "user", "company"]
    list_filter = ["model_name"]
    search_fields = ["model_name", "field_name"]
    readonly_fields = ["id", "created_at", "updated_at"]
    autocomplete_fields = ["user", "company"]


@admin.register(SavedFilter)
class SavedFilterAdmin(admin.ModelAdmin):
    list_display = ["name", "model_name", "user", "company", "is_default"]
    list_filter = ["model_name", "is_default"]
    search_fields = ["name", "model_name"]
    readonly_fields = ["id", "created_at", "updated_at"]
    autocomplete_fields = ["user", "company"]


@admin.register(LoginLog)
class LoginLogAdmin(admin.ModelAdmin):
    list_display = ["event", "user", "username_attempted", "ip_address", "timestamp"]
    list_filter = ["event"]
    search_fields = ["username_attempted", "ip_address", "user__username"]
    readonly_fields = ["id", "timestamp", "user", "event", "ip_address", "user_agent", "api_key"]
    date_hierarchy = "timestamp"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(UserPreferences)
class UserPreferencesAdmin(admin.ModelAdmin):
    list_display = ["user", "language", "timezone", "theme", "email_digest"]
    search_fields = ["user__username"]
    readonly_fields = ["id", "created_at", "updated_at"]
    autocomplete_fields = ["user", "language", "currency", "default_company"]


@admin.register(Bank)
class BankAdmin(admin.ModelAdmin):
    list_display = ["name", "bic", "country", "is_active"]
    list_filter = ["is_active", "country"]
    search_fields = ["name", "bic"]
    readonly_fields = ["id", "created_at", "updated_at"]
    autocomplete_fields = ["country"]


@admin.register(PartnerBank)
class PartnerBankAdmin(admin.ModelAdmin):
    list_display = ["acc_number", "acc_type", "partner", "bank", "currency", "is_primary"]
    list_filter = ["acc_type", "is_primary"]
    search_fields = ["acc_number", "partner__name", "bank__name"]
    readonly_fields = ["id", "created_at", "updated_at"]
    autocomplete_fields = ["partner", "bank", "currency"]


@admin.register(DecimalPrecision)
class DecimalPrecisionAdmin(admin.ModelAdmin):
    list_display = ["name", "company", "digits"]
    list_filter = ["company"]
    search_fields = ["name"]
    readonly_fields = ["id", "created_at", "updated_at"]
    autocomplete_fields = ["company"]
