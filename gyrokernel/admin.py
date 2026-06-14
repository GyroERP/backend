"""Django admin configuration for GyroKernel models."""

from django.contrib import admin

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
    SequenceDateRange,
    SystemParameter,
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
