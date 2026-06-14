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
]
