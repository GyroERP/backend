"""
gyro_seed — populate ISO master data into the database.

Usage:
    python manage.py gyro_seed                  # seed everything
    python manage.py gyro_seed --only currencies
    python manage.py gyro_seed --only languages
    python manage.py gyro_seed --only countries
    python manage.py gyro_seed --force          # re-seed existing records
"""

from __future__ import annotations

import decimal

from django.core.management.base import BaseCommand

# ---------------------------------------------------------------------------
# Static enrichment data
# ---------------------------------------------------------------------------

# Major currencies: (iso_code, name, symbol, symbol_position, decimal_places, rounding)
_CURRENCY_DATA: dict[str, tuple] = {
    "USD": ("US Dollar", "$", "before", 2, "0.01"),
    "EUR": ("Euro", "€", "after", 2, "0.01"),
    "GBP": ("British Pound", "£", "before", 2, "0.01"),
    "JPY": ("Japanese Yen", "¥", "before", 0, "1"),
    "CNY": ("Chinese Yuan", "¥", "before", 2, "0.01"),
    "INR": ("Indian Rupee", "₹", "before", 2, "0.01"),
    "CAD": ("Canadian Dollar", "CA$", "before", 2, "0.01"),
    "AUD": ("Australian Dollar", "A$", "before", 2, "0.01"),
    "CHF": ("Swiss Franc", "CHF", "before", 2, "0.05"),
    "HKD": ("Hong Kong Dollar", "HK$", "before", 2, "0.01"),
    "SGD": ("Singapore Dollar", "S$", "before", 2, "0.01"),
    "SEK": ("Swedish Krona", "kr", "after", 2, "0.01"),
    "NOK": ("Norwegian Krone", "kr", "after", 2, "0.01"),
    "DKK": ("Danish Krone", "kr", "after", 2, "0.01"),
    "NZD": ("New Zealand Dollar", "NZ$", "before", 2, "0.01"),
    "MXN": ("Mexican Peso", "$", "before", 2, "0.01"),
    "BRL": ("Brazilian Real", "R$", "before", 2, "0.01"),
    "RUB": ("Russian Ruble", "₽", "after", 2, "0.01"),
    "ZAR": ("South African Rand", "R", "before", 2, "0.01"),
    "TRY": ("Turkish Lira", "₺", "before", 2, "0.01"),
    "AED": ("UAE Dirham", "د.إ", "before", 2, "0.01"),
    "SAR": ("Saudi Riyal", "﷼", "before", 2, "0.01"),
    "THB": ("Thai Baht", "฿", "before", 2, "0.01"),
    "IDR": ("Indonesian Rupiah", "Rp", "before", 0, "1"),
    "MYR": ("Malaysian Ringgit", "RM", "before", 2, "0.01"),
    "PHP": ("Philippine Peso", "₱", "before", 2, "0.01"),
    "VND": ("Vietnamese Dong", "₫", "after", 0, "1"),
    "KRW": ("South Korean Won", "₩", "before", 0, "1"),
    "TWD": ("New Taiwan Dollar", "NT$", "before", 0, "1"),
    "PKR": ("Pakistani Rupee", "₨", "before", 2, "0.01"),
    "BDT": ("Bangladeshi Taka", "৳", "before", 2, "0.01"),
    "EGP": ("Egyptian Pound", "E£", "before", 2, "0.01"),
    "NGN": ("Nigerian Naira", "₦", "before", 2, "0.01"),
    "KES": ("Kenyan Shilling", "KSh", "before", 2, "0.01"),
    "GHS": ("Ghanaian Cedi", "₵", "before", 2, "0.01"),
    "MAD": ("Moroccan Dirham", "MAD", "before", 2, "0.01"),
    "ILS": ("Israeli Shekel", "₪", "before", 2, "0.01"),
    "QAR": ("Qatari Riyal", "﷼", "before", 2, "0.01"),
    "KWD": ("Kuwaiti Dinar", "KD", "before", 3, "0.001"),
    "BHD": ("Bahraini Dinar", "BD", "before", 3, "0.001"),
    "OMR": ("Omani Rial", "﷼", "before", 3, "0.001"),
    "JOD": ("Jordanian Dinar", "JD", "before", 3, "0.001"),
    "CLP": ("Chilean Peso", "$", "before", 0, "1"),
    "COP": ("Colombian Peso", "$", "before", 0, "1"),
    "ARS": ("Argentine Peso", "$", "before", 2, "0.01"),
    "PEN": ("Peruvian Sol", "S/", "before", 2, "0.01"),
    "CZK": ("Czech Koruna", "Kč", "after", 2, "0.01"),
    "HUF": ("Hungarian Forint", "Ft", "after", 0, "1"),
    "PLN": ("Polish Zloty", "zł", "after", 2, "0.01"),
    "RON": ("Romanian Leu", "lei", "after", 2, "0.01"),
    "BGN": ("Bulgarian Lev", "лв", "after", 2, "0.01"),
    "HRK": ("Croatian Kuna", "kn", "after", 2, "0.01"),
    "UAH": ("Ukrainian Hryvnia", "₴", "before", 2, "0.01"),
    "ISK": ("Icelandic Króna", "kr", "after", 0, "1"),
    "IRR": ("Iranian Rial", "﷼", "before", 0, "1"),
    "IQD": ("Iraqi Dinar", "ع.د", "before", 3, "0.001"),
    "LBP": ("Lebanese Pound", "ل.ل", "before", 0, "1"),
    "XAF": ("CFA Franc BEAC", "FCFA", "before", 0, "1"),
    "XOF": ("CFA Franc BCEAO", "CFA", "before", 0, "1"),
    "XCD": ("East Caribbean Dollar", "EC$", "before", 2, "0.01"),
    "XPF": ("CFP Franc", "CFP", "before", 0, "1"),
}

# RTL language iso codes
_RTL_CODES = {"ar", "he", "fa", "ur", "yi", "dv", "ku", "ps", "sd", "ug"}

# Languages: (code, name, iso_code, url_code, date_format, time_format, decimal_point, thousands_sep, week_start)
_LANGUAGE_DATA = [
    ("en_US", "English (US)", "en", "en", "%m/%d/%Y", "%I:%M:%S %p", ".", ",", 6),
    ("en_GB", "English (UK)", "en", "en_GB", "%d/%m/%Y", "%H:%M:%S", ".", ",", 0),
    ("fr_FR", "French", "fr", "fr", "%d/%m/%Y", "%H:%M:%S", ",", ".", 0),
    ("de_DE", "German", "de", "de", "%d.%m.%Y", "%H:%M:%S", ",", ".", 0),
    ("es_ES", "Spanish", "es", "es", "%d/%m/%Y", "%H:%M:%S", ",", ".", 0),
    ("es_MX", "Spanish (Mexico)", "es", "es_MX", "%d/%m/%Y", "%H:%M:%S", ".", ",", 0),
    ("pt_BR", "Portuguese (Brazil)", "pt", "pt_BR", "%d/%m/%Y", "%H:%M:%S", ",", ".", 0),
    ("pt_PT", "Portuguese (Portugal)", "pt", "pt_PT", "%d/%m/%Y", "%H:%M:%S", ",", ".", 0),
    ("it_IT", "Italian", "it", "it", "%d/%m/%Y", "%H:%M:%S", ",", ".", 0),
    ("nl_NL", "Dutch", "nl", "nl", "%d-%m-%Y", "%H:%M:%S", ",", ".", 0),
    ("ru_RU", "Russian", "ru", "ru", "%d.%m.%Y", "%H:%M:%S", ",", ".", 0),
    ("zh_CN", "Chinese (Simplified)", "zh", "zh_CN", "%Y/%m/%d", "%H:%M:%S", ".", ",", 0),
    ("zh_TW", "Chinese (Traditional)", "zh", "zh_TW", "%Y/%m/%d", "%H:%M:%S", ".", ",", 0),
    ("ja_JP", "Japanese", "ja", "ja", "%Y/%m/%d", "%H:%M:%S", ".", ",", 0),
    ("ko_KR", "Korean", "ko", "ko", "%Y.%m.%d", "%H:%M:%S", ".", ",", 0),
    ("ar_SA", "Arabic", "ar", "ar", "%d/%m/%Y", "%H:%M:%S", ".", ",", 6),
    ("he_IL", "Hebrew", "he", "he", "%d/%m/%Y", "%H:%M:%S", ".", ",", 0),
    ("fa_IR", "Persian (Farsi)", "fa", "fa", "%Y/%m/%d", "%H:%M:%S", ".", ",", 6),
    ("ur_PK", "Urdu", "ur", "ur", "%d/%m/%Y", "%H:%M:%S", ".", ",", 0),
    ("hi_IN", "Hindi", "hi", "hi", "%d/%m/%Y", "%H:%M:%S", ".", ",", 0),
    ("tr_TR", "Turkish", "tr", "tr", "%d.%m.%Y", "%H:%M:%S", ",", ".", 0),
    ("pl_PL", "Polish", "pl", "pl", "%d.%m.%Y", "%H:%M:%S", ",", ".", 0),
    ("cs_CZ", "Czech", "cs", "cs", "%d.%m.%Y", "%H:%M:%S", ",", ".", 0),
    ("sk_SK", "Slovak", "sk", "sk", "%d.%m.%Y", "%H:%M:%S", ",", ".", 0),
    ("hu_HU", "Hungarian", "hu", "hu", "%Y.%m.%d.", "%H:%M:%S", ",", ".", 0),
    ("ro_RO", "Romanian", "ro", "ro", "%d.%m.%Y", "%H:%M:%S", ",", ".", 0),
    ("bg_BG", "Bulgarian", "bg", "bg", "%d.%m.%Y", "%H:%M:%S", ",", ".", 0),
    ("hr_HR", "Croatian", "hr", "hr", "%d.%m.%Y", "%H:%M:%S", ",", ".", 0),
    ("sv_SE", "Swedish", "sv", "sv", "%Y-%m-%d", "%H:%M:%S", ",", ".", 0),
    ("nb_NO", "Norwegian", "nb", "nb", "%d.%m.%Y", "%H:%M:%S", ",", ".", 0),
    ("da_DK", "Danish", "da", "da", "%d.%m.%Y", "%H:%M:%S", ",", ".", 0),
    ("fi_FI", "Finnish", "fi", "fi", "%d.%m.%Y", "%H:%M:%S", ",", ".", 0),
    ("el_GR", "Greek", "el", "el", "%d/%m/%Y", "%H:%M:%S", ",", ".", 0),
    ("uk_UA", "Ukrainian", "uk", "uk", "%d.%m.%Y", "%H:%M:%S", ",", ".", 0),
    ("vi_VN", "Vietnamese", "vi", "vi", "%d/%m/%Y", "%H:%M:%S", ",", ".", 0),
    ("th_TH", "Thai", "th", "th", "%d/%m/%Y", "%H:%M:%S", ".", ",", 0),
    ("id_ID", "Indonesian", "id", "id", "%d/%m/%Y", "%H:%M:%S", ",", ".", 0),
    ("ms_MY", "Malay", "ms", "ms", "%d/%m/%Y", "%H:%M:%S", ".", ",", 0),
    ("ca_ES", "Catalan", "ca", "ca", "%d/%m/%Y", "%H:%M:%S", ",", ".", 0),
    ("af_ZA", "Afrikaans", "af", "af", "%d/%m/%Y", "%H:%M:%S", ",", ".", 0),
]


class Command(BaseCommand):
    help = "Seed ISO master data: currencies, languages, countries, and states."

    def add_arguments(self, parser):
        parser.add_argument(
            "--only",
            choices=["currencies", "languages", "countries", "all"],
            default="all",
            help="Which data set to seed (default: all)",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Re-seed existing records (update_or_create)",
        )

    def handle(self, *args, **options):
        only = options["only"]
        force = options["force"]

        if only in ("currencies", "all"):
            self._seed_currencies(force)
        if only in ("languages", "all"):
            self._seed_languages(force)
        if only in ("countries", "all"):
            self._seed_countries(force)

        self.stdout.write(self.style.SUCCESS("gyro_seed complete."))

    # ------------------------------------------------------------------
    # Currencies
    # ------------------------------------------------------------------

    def _seed_currencies(self, force: bool) -> None:
        import pycountry

        from gyrokernel.models import Currency

        created = updated = skipped = 0

        # Build full set: static enrichment + pycountry fallback
        all_codes: set[str] = set(_CURRENCY_DATA) | {
            c.alpha_3 for c in pycountry.currencies
        }

        for iso_code in sorted(all_codes):
            static = _CURRENCY_DATA.get(iso_code)
            if static:
                name, symbol, pos, dp, rounding = static
            else:
                pc = pycountry.currencies.get(alpha_3=iso_code)
                if not pc:
                    continue
                name = pc.name
                symbol = iso_code
                pos = "before"
                dp = 2
                rounding = "0.01"

            defaults = {
                "name": name,
                "symbol": symbol,
                "symbol_position": pos,
                "decimal_places": dp,
                "rounding": decimal.Decimal(rounding),
                "is_active": True,
            }

            if force:
                obj, was_created = Currency.objects.update_or_create(
                    iso_code=iso_code, defaults=defaults
                )
                if was_created:
                    created += 1
                else:
                    updated += 1
            else:
                obj, was_created = Currency.objects.get_or_create(
                    iso_code=iso_code, defaults=defaults
                )
                if was_created:
                    created += 1
                else:
                    skipped += 1

        self.stdout.write(
            f"  Currencies: {created} created, {updated} updated, {skipped} skipped."
        )

    # ------------------------------------------------------------------
    # Languages
    # ------------------------------------------------------------------

    def _seed_languages(self, force: bool) -> None:
        from gyrokernel.models import Language, TextDirection

        created = updated = skipped = 0

        for row in _LANGUAGE_DATA:
            code, name, iso_code, url_code, dfmt, tfmt, dp, ts, week_start = row
            direction = TextDirection.RTL if iso_code in _RTL_CODES else TextDirection.LTR

            defaults = {
                "name": name,
                "iso_code": iso_code,
                "url_code": url_code,
                "direction": direction,
                "date_format": dfmt,
                "time_format": tfmt,
                "decimal_point": dp,
                "thousands_separator": ts,
                "week_start": week_start,
                "is_active": True,
            }

            if force:
                obj, was_created = Language.objects.update_or_create(code=code, defaults=defaults)
                if was_created:
                    created += 1
                else:
                    updated += 1
            else:
                obj, was_created = Language.objects.get_or_create(code=code, defaults=defaults)
                if was_created:
                    created += 1
                else:
                    skipped += 1

        self.stdout.write(
            f"  Languages: {created} created, {updated} updated, {skipped} skipped."
        )

    # ------------------------------------------------------------------
    # Countries + States
    # ------------------------------------------------------------------

    def _seed_countries(self, force: bool) -> None:
        import pycountry

        from gyrokernel.models import Country, CountryState, Currency

        # Build iso_code → Currency pk map for fast FK assignment
        currency_map: dict[str, object] = {
            c.iso_code: c for c in Currency.objects.only("id", "iso_code")
        }

        c_created = c_updated = c_skipped = 0
        s_created = s_skipped = 0

        for pc in pycountry.countries:
            alpha2 = pc.alpha_2
            alpha3 = getattr(pc, "alpha_3", "")
            numeric = getattr(pc, "numeric", "")

            # Find default currency via pycountry (not 100% coverage)
            currency_obj = None
            try:
                for pc_curr in pycountry.currencies:
                    # pycountry doesn't link country→currency directly;
                    # skip this — currency stays null and can be set by admin
                    pass
            except Exception:
                pass

            defaults = {
                "name": pc.name,
                "alpha3": alpha3,
                "numeric_code": numeric,
                "is_active": True,
            }

            if force:
                country_obj, was_created = Country.objects.update_or_create(
                    code=alpha2, defaults=defaults
                )
                if was_created:
                    c_created += 1
                else:
                    c_updated += 1
            else:
                country_obj, was_created = Country.objects.get_or_create(
                    code=alpha2, defaults=defaults
                )
                if was_created:
                    c_created += 1
                else:
                    c_skipped += 1

            # Seed subdivisions (states)
            subdivisions = pycountry.subdivisions.get(country_code=alpha2) or []
            for sub in subdivisions:
                # Use only first-level subdivisions (no parent)
                if getattr(sub, "parent_code", None):
                    continue
                state_code = sub.code.split("-")[-1]  # "US-CA" → "CA"
                state_defaults = {"name": sub.name}

                if force:
                    _, st_created = CountryState.objects.update_or_create(
                        country=country_obj,
                        code=state_code,
                        defaults=state_defaults,
                    )
                else:
                    _, st_created = CountryState.objects.get_or_create(
                        country=country_obj,
                        code=state_code,
                        defaults=state_defaults,
                    )
                if st_created:
                    s_created += 1
                else:
                    s_skipped += 1

        self.stdout.write(
            f"  Countries: {c_created} created, {c_updated} updated, {c_skipped} skipped."
        )
        self.stdout.write(
            f"  States:    {s_created} created, {s_skipped} skipped."
        )
