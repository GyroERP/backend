"""Tests for Currency and CurrencyRate models."""

import decimal
from datetime import date

import pytest

from gyrokernel.models import Currency, CurrencyRate


@pytest.fixture
def usd(db):
    return Currency.objects.create(
        name="US Dollar", iso_code="USD", symbol="$",
        symbol_position="before", decimal_places=2,
        rounding=decimal.Decimal("0.01"),
    )


@pytest.fixture
def eur(db):
    return Currency.objects.create(
        name="Euro", iso_code="EUR", symbol="€",
        symbol_position="after", decimal_places=2,
        rounding=decimal.Decimal("0.01"),
    )


@pytest.fixture
def jpy(db):
    return Currency.objects.create(
        name="Japanese Yen", iso_code="JPY", symbol="¥",
        symbol_position="before", decimal_places=0,
        rounding=decimal.Decimal("1"),
    )


@pytest.mark.django_db
class TestCurrency:
    def test_str_is_iso_code(self, usd):
        assert str(usd) == "USD"

    def test_round_usd(self, usd):
        assert usd.round(decimal.Decimal("1.234")) == decimal.Decimal("1.23")
        assert usd.round(decimal.Decimal("1.235")) == decimal.Decimal("1.24")

    def test_round_jpy_no_decimals(self, jpy):
        assert jpy.round(decimal.Decimal("1234.5")) == decimal.Decimal("1235")

    def test_is_zero_true(self, usd):
        assert usd.is_zero(decimal.Decimal("0.001")) is True

    def test_is_zero_false(self, usd):
        assert usd.is_zero(decimal.Decimal("0.01")) is False

    def test_format_amount_before(self, usd):
        result = usd.format_amount(decimal.Decimal("1234.5"))
        assert result.startswith("$")
        assert "1,234.50" in result

    def test_format_amount_after(self, eur):
        result = eur.format_amount(decimal.Decimal("999.99"))
        assert result.endswith("€") or "€" in result

    def test_convert_same_currency_returns_rounded(self, usd):
        result = usd.convert(decimal.Decimal("100.123"), usd)
        assert result == decimal.Decimal("100.12")

    def test_convert_usd_to_eur(self, usd, eur):
        # 1 USD = 1.0 USD; 1 EUR = 1.1 USD → 100 USD = ~90.91 EUR
        CurrencyRate.objects.create(currency=usd, rate=decimal.Decimal("1.0"), date=date.today())
        CurrencyRate.objects.create(currency=eur, rate=decimal.Decimal("1.1"), date=date.today())

        result = usd.convert(decimal.Decimal("100"), eur)
        expected = eur.round(decimal.Decimal("100") * decimal.Decimal("1.0") / decimal.Decimal("1.1"))
        assert result == expected

    def test_convert_no_rate_raises(self, usd, eur):
        with pytest.raises(ValueError, match="No exchange rate"):
            usd.convert(decimal.Decimal("100"), eur)


@pytest.mark.django_db
class TestCurrencyRate:
    def test_rate_date_lookup_uses_latest_on_or_before(self, usd):
        CurrencyRate.objects.create(
            currency=usd, rate=decimal.Decimal("0.9"), date=date(2024, 1, 1)
        )
        CurrencyRate.objects.create(
            currency=usd, rate=decimal.Decimal("1.0"), date=date(2024, 6, 1)
        )

        # Looking up on 2024-07-01 should return the June rate (1.0)
        rate = usd._get_rate(date=date(2024, 7, 1))
        assert rate == decimal.Decimal("1.0")

    def test_rate_falls_back_to_global_when_no_company_rate(self, usd):
        CurrencyRate.objects.create(
            currency=usd, rate=decimal.Decimal("1.0"), date=date.today()
        )
        # No company-specific rate — should return global
        rate = usd._get_rate(company=None, date=date.today())
        assert rate == decimal.Decimal("1.0")

    def test_no_rate_returns_none(self, usd):
        assert usd._get_rate(date=date(2020, 1, 1)) is None

    def test_str_representation(self, usd):
        r = CurrencyRate.objects.create(
            currency=usd, rate=decimal.Decimal("1.0"), date=date(2024, 1, 1)
        )
        assert "USD" in str(r)
        assert "1.0" in str(r)
