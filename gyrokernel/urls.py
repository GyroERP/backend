"""URL routing for the GyroERP kernel API."""

from rest_framework.routers import DefaultRouter

from gyrokernel.viewsets.base import (
    AttachmentViewSet,
    AuditLogViewSet,
    CompanyViewSet,
    CountryStateViewSet,
    CountryViewSet,
    CurrencyRateViewSet,
    CurrencyViewSet,
    InstalledAppViewSet,
    LanguageViewSet,
    PartnerTagViewSet,
    PartnerViewSet,
    RecordRuleViewSet,
    SequenceViewSet,
    SystemParameterViewSet,
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

urlpatterns = router.urls
