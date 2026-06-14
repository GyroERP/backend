"""Tests for FieldDefault, SavedFilter, Bank/PartnerBank, DecimalPrecision."""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from gyrokernel.models import (
    Bank,
    Country,
    Currency,
    DecimalPrecision,
    FieldDefault,
    Partner,
    PartnerBank,
    PartnerType,
    SavedFilter,
)

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="misc_user", password="pass")


@pytest.fixture
def country(db):
    return Country.objects.create(name="United States", code="US", alpha3="USA")


# ---------------------------------------------------------------------------
# FieldDefault
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestFieldDefault:
    def test_set_and_get_global_default(self):
        FieldDefault.set("sales.SalesOrder", "warehouse_id", "main_wh")
        result = FieldDefault.get("sales.SalesOrder", "warehouse_id")
        assert result == "main_wh"

    def test_get_returns_builtin_default_when_not_set(self):
        result = FieldDefault.get("sales.SalesOrder", "nonexistent_field", default="fallback")
        assert result == "fallback"

    def test_user_specific_overrides_global(self, user):
        FieldDefault.set("sales.SalesOrder", "warehouse_id", "global_wh")
        FieldDefault.set("sales.SalesOrder", "warehouse_id", "user_wh", user=user)
        assert FieldDefault.get("sales.SalesOrder", "warehouse_id", user=user) == "user_wh"
        # Another user still sees global
        other = User.objects.create_user(username="other", password="x")
        assert FieldDefault.get("sales.SalesOrder", "warehouse_id", user=other) == "global_wh"

    def test_clear_removes_entry(self):
        FieldDefault.set("test.Model", "field_x", 99)
        FieldDefault.clear("test.Model", "field_x")
        assert FieldDefault.get("test.Model", "field_x") is None

    def test_value_property_decodes_json(self):
        fd = FieldDefault(model_name="x", field_name="y", json_value='{"k": 1}')
        assert fd.value == {"k": 1}

    def test_str_representation(self):
        fd = FieldDefault(model_name="sales.SalesOrder", field_name="warehouse_id", json_value='"wh"')
        assert "sales.SalesOrder" in str(fd)
        assert "warehouse_id" in str(fd)


# ---------------------------------------------------------------------------
# SavedFilter
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestSavedFilter:
    def test_create_saved_filter(self, user):
        sf = SavedFilter.objects.create(
            name="My Orders",
            model_name="sales.SalesOrder",
            user=user,
        )
        assert sf.pk is not None

    def test_is_default_unsets_previous_default(self, user):
        sf1 = SavedFilter.objects.create(
            name="Filter 1", model_name="sales.SalesOrder", user=user, is_default=True,
        )
        sf2 = SavedFilter.objects.create(
            name="Filter 2", model_name="sales.SalesOrder", user=user, is_default=True,
        )
        sf1.refresh_from_db()
        assert sf1.is_default is False
        assert sf2.is_default is True

    def test_get_defaults_for_model(self, user):
        SavedFilter.objects.create(
            name="Default Filter", model_name="sales.SalesOrder", user=user, is_default=True,
        )
        defaults = SavedFilter.get_defaults("sales.SalesOrder", user=user)
        assert defaults.count() == 1

    def test_str_representation(self, user):
        sf = SavedFilter(name="Test", model_name="sales.SalesOrder", user=user)
        assert "Test" in str(sf)


# ---------------------------------------------------------------------------
# Bank + PartnerBank
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestBanking:
    def test_create_bank(self, country):
        bank = Bank.objects.create(name="Deutsche Bank", bic="DEUTDEDB", country=country)
        assert "DEUTDEDB" in str(bank)

    def test_bank_without_bic(self, country):
        bank = Bank.objects.create(name="Local Credit Union", country=country)
        assert "Local Credit Union" in str(bank)

    def test_create_partner_bank(self, country):
        partner = Partner.objects.create(
            name="Acme Corp", partner_type=PartnerType.COMPANY, is_company=True, country=country
        )
        bank = Bank.objects.create(name="Bank of America", country=country)
        pb = PartnerBank.objects.create(
            partner=partner,
            bank=bank,
            acc_number="DE89370400440532013000",
            acc_type="iban",
            is_primary=True,
        )
        assert pb.is_primary is True

    def test_primary_enforced_single_per_partner(self, country):
        partner = Partner.objects.create(
            name="Corp", partner_type=PartnerType.COMPANY, is_company=True, country=country
        )
        bank = Bank.objects.create(name="Bank A", country=country)
        pb1 = PartnerBank.objects.create(
            partner=partner, bank=bank, acc_number="ACC001", is_primary=True
        )
        pb2 = PartnerBank.objects.create(
            partner=partner, bank=bank, acc_number="ACC002", is_primary=True
        )
        pb1.refresh_from_db()
        assert pb1.is_primary is False
        assert pb2.is_primary is True

    def test_str_representation(self, country):
        bank = Bank.objects.create(name="First Bank", bic="FIRSTUS", country=country)
        partner = Partner.objects.create(
            name="Corp", partner_type=PartnerType.COMPANY, is_company=True, country=country
        )
        pb = PartnerBank(partner=partner, bank=bank, acc_number="ACC999")
        assert "ACC999" in str(pb)


# ---------------------------------------------------------------------------
# DecimalPrecision
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestDecimalPrecision:
    def test_ensure_creates_global_row(self):
        dp = DecimalPrecision.ensure("Product Price", digits=2)
        assert dp.digits == 2
        assert dp.company is None

    def test_ensure_idempotent(self):
        DecimalPrecision.ensure("Product Price", digits=2)
        DecimalPrecision.ensure("Product Price", digits=2)
        assert DecimalPrecision.objects.filter(name="Product Price").count() == 1

    def test_get_digits_global(self):
        DecimalPrecision.objects.create(name="Discount", digits=4)
        assert DecimalPrecision.get_digits("Discount") == 4

    def test_get_digits_default_when_not_found(self):
        assert DecimalPrecision.get_digits("Unknown Precision", default=6) == 6

    def test_str_representation(self):
        dp = DecimalPrecision(name="Product Price", digits=2)
        assert "Product Price" in str(dp)
        assert "2" in str(dp)
