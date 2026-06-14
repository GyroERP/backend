"""URL routing for the GyroERP kernel API."""

from rest_framework.routers import DefaultRouter

from gyrokernel.viewsets.base import (
    APIKeyViewSet,
    AttachmentViewSet,
    AuditLogViewSet,
    BankViewSet,
    CompanyViewSet,
    CountryStateViewSet,
    CountryViewSet,
    CurrencyRateViewSet,
    CurrencyViewSet,
    DecimalPrecisionViewSet,
    FieldDefaultViewSet,
    GroupExtensionViewSet,
    InstalledAppViewSet,
    LanguageViewSet,
    LoginLogViewSet,
    MailServerViewSet,
    ModelPermissionViewSet,
    PartnerBankViewSet,
    PartnerTagViewSet,
    PartnerViewSet,
    RecordRuleViewSet,
    SavedFilterViewSet,
    SequenceViewSet,
    SystemParameterViewSet,
    UserPreferencesViewSet,
)

router = DefaultRouter()

# Phase 1
router.register("companies", CompanyViewSet, basename="company")
router.register("apps", InstalledAppViewSet, basename="installed-app")
router.register("params", SystemParameterViewSet, basename="system-parameter")
router.register("audit-log", AuditLogViewSet, basename="audit-log")

# Phase 2
router.register("currencies", CurrencyViewSet, basename="currency")
router.register("currency-rates", CurrencyRateViewSet, basename="currency-rate")
router.register("languages", LanguageViewSet, basename="language")
router.register("countries", CountryViewSet, basename="country")
router.register("country-states", CountryStateViewSet, basename="country-state")
router.register("sequences", SequenceViewSet, basename="sequence")
router.register("partner-tags", PartnerTagViewSet, basename="partner-tag")
router.register("partners", PartnerViewSet, basename="partner")
router.register("record-rules", RecordRuleViewSet, basename="record-rule")
router.register("attachments", AttachmentViewSet, basename="attachment")

# Phase 3
router.register("model-permissions", ModelPermissionViewSet, basename="model-permission")
router.register("group-extensions", GroupExtensionViewSet, basename="group-extension")
router.register("api-keys", APIKeyViewSet, basename="api-key")
router.register("mail-servers", MailServerViewSet, basename="mail-server")
router.register("field-defaults", FieldDefaultViewSet, basename="field-default")
router.register("saved-filters", SavedFilterViewSet, basename="saved-filter")
router.register("login-log", LoginLogViewSet, basename="login-log")
router.register("user-preferences", UserPreferencesViewSet, basename="user-preferences")
router.register("banks", BankViewSet, basename="bank")
router.register("partner-banks", PartnerBankViewSet, basename="partner-bank")
router.register("decimal-precisions", DecimalPrecisionViewSet, basename="decimal-precision")

urlpatterns = router.urls
