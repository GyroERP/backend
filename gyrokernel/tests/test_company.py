"""Tests for the Company (tenant) model."""

import pytest
from django.db import IntegrityError

from gyrokernel.models import Company, Country, Currency


@pytest.fixture
def us_country(db):
    return Country.objects.create(name="United States", code="US", alpha3="USA")


@pytest.fixture
def usd_currency(db):
    return Currency.objects.create(name="US Dollar", iso_code="USD", symbol="$")


@pytest.mark.django_db
class TestCompany:
    def test_create_minimal(self, us_country):
        company = Company.objects.create(name="GyroERP Inc.", code="GYRO", country=us_country)
        assert company.pk is not None
        assert str(company) == "GyroERP Inc. (GYRO)"

    def test_country_is_fk(self, us_country):
        company = Company.objects.create(name="FK Test", code="FKT", country=us_country)
        assert company.country_id == us_country.pk
        assert company.country.code == "US"

    def test_currency_is_fk(self, us_country, usd_currency):
        company = Company.objects.create(
            name="Currency Co", code="CURR", country=us_country, currency=usd_currency
        )
        assert company.currency.iso_code == "USD"

    def test_currency_defaults_to_null(self, us_country):
        company = Company.objects.create(name="NoCurr", code="NCR", country=us_country)
        assert company.currency is None

    def test_default_timezone_is_utc(self, us_country):
        company = Company.objects.create(name="TZ Co", code="TZC", country=us_country)
        assert company.timezone == "UTC"

    def test_default_is_active(self, us_country):
        company = Company.objects.create(name="Active", code="ACT", country=us_country)
        assert company.is_active is True

    def test_code_is_unique(self, us_country):
        Company.objects.create(name="First", code="UNIQ", country=us_country)
        with pytest.raises(IntegrityError):
            Company.objects.create(name="Second", code="UNIQ", country=us_country)

    def test_parent_subsidiary_relationship(self, us_country):
        parent = Company.objects.create(name="HoldCo", code="HOLD", country=us_country)
        sub = Company.objects.create(name="SubCo", code="SUB", country=us_country, parent=parent)

        assert sub.is_subsidiary is True
        assert parent.is_subsidiary is False
        assert parent.subsidiaries.filter(code="SUB").exists()

    def test_root_company_has_no_parent(self, us_country):
        company = Company.objects.create(name="Root", code="ROOT", country=us_country)
        assert company.parent is None

    def test_active_filter(self, us_country):
        Company.objects.create(name="On", code="ON1", country=us_country, is_active=True)
        Company.objects.create(name="Off", code="OFF1", country=us_country, is_active=False)

        assert Company.objects.filter(is_active=True, code="ON1").exists()
        assert Company.objects.filter(is_active=False, code="OFF1").exists()

    def test_address_fields(self, us_country):
        company = Company.objects.create(
            name="Addr Co", code="ADDR",
            country=us_country,
            street="123 Main St", city="Springfield", zip_code="12345",
            email="info@addr.co", phone="+1234567890", vat="US123456789",
        )
        assert company.street == "123 Main St"
        assert company.email == "info@addr.co"
        assert company.vat == "US123456789"

    def test_str_representation(self, us_country):
        company = Company.objects.create(name="Acme Corp", code="ACME", country=us_country)
        assert str(company) == "Acme Corp (ACME)"
