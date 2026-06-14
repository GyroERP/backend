"""GyroKernel models — public surface for the kernel package."""

# Abstract base classes — import these in business app models
from .base import (
    ActiveModel,
    AllObjectsManager,
    AuditModel,
    GyroBaseModel,
    SoftDeleteManager,
    SoftDeleteModel,
    SoftDeleteQuerySet,
    TimestampedModel,
    UUIDModel,
)

# Concrete kernel models — Phase 1
from .audit import AuditAction, AuditLog
from .company import Company
from .config import SystemParameter
from .registry import AppState, InstalledApp

# Concrete kernel models — Phase 2: master data
from .currency import Currency, CurrencyRate, SymbolPosition
from .language import Language, TextDirection
from .country import Country, CountryState

# Concrete kernel models — Phase 2: sequences
from .sequence import Sequence, SequenceDateRange, SequenceImplementation

# Concrete kernel models — Phase 2: partners
from .partner import AddressType, Partner, PartnerTag, PartnerType

# Concrete kernel models — Phase 2: access control
from .access import RecordRule

# Concrete kernel models — Phase 2: attachments
from .attachment import Attachment

# Concrete kernel models — Phase 3: security
from .access_control import GroupExtension, ModelPermission, get_effective_group_ids, get_effective_groups
from .apikey import APIKey, APIKeyScope

# Concrete kernel models — Phase 3: communication
from .mail_server import MailEncryption, MailServer

# Concrete kernel models — Phase 3: UX
from .field_default import FieldDefault
from .saved_filter import SavedFilter

# Concrete kernel models — Phase 3: user
from .user_ext import (
    DisplayDensity,
    EmailDigestFrequency,
    FontSize,
    LoginEvent,
    LoginLog,
    Theme,
    UserPreferences,
)

# Concrete kernel models — Phase 3: banking
from .banking import AccountType, Bank, PartnerBank

# Concrete kernel models — Phase 3: precision
from .decimal_precision import DecimalPrecision

__all__ = [
    # Abstract
    "UUIDModel",
    "TimestampedModel",
    "AuditModel",
    "SoftDeleteQuerySet",
    "SoftDeleteManager",
    "AllObjectsManager",
    "SoftDeleteModel",
    "ActiveModel",
    "GyroBaseModel",
    # Phase 1 concrete
    "Company",
    "InstalledApp",
    "AppState",
    "SystemParameter",
    "AuditLog",
    "AuditAction",
    # Phase 2: currency
    "Currency",
    "CurrencyRate",
    "SymbolPosition",
    # Phase 2: language
    "Language",
    "TextDirection",
    # Phase 2: country
    "Country",
    "CountryState",
    # Phase 2: sequence
    "Sequence",
    "SequenceDateRange",
    "SequenceImplementation",
    # Phase 2: partner
    "Partner",
    "PartnerTag",
    "PartnerType",
    "AddressType",
    # Phase 2: access
    "RecordRule",
    # Phase 2: attachment
    "Attachment",
    # Phase 3: security
    "ModelPermission",
    "GroupExtension",
    "get_effective_group_ids",
    "get_effective_groups",
    "APIKey",
    "APIKeyScope",
    # Phase 3: communication
    "MailServer",
    "MailEncryption",
    # Phase 3: UX
    "FieldDefault",
    "SavedFilter",
    # Phase 3: user
    "LoginLog",
    "LoginEvent",
    "UserPreferences",
    "EmailDigestFrequency",
    "DisplayDensity",
    "Theme",
    "FontSize",
    # Phase 3: banking
    "Bank",
    "PartnerBank",
    "AccountType",
    # Phase 3: precision
    "DecimalPrecision",
]
