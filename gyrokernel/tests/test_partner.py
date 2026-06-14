"""Tests for Partner, PartnerTag, and the materialized path tree."""

import pytest

from gyrokernel.models import Country, Partner, PartnerTag, PartnerType


@pytest.fixture
def country(db):
    return Country.objects.create(name="United States", code="US", alpha3="USA")


@pytest.fixture
def acme(db, country):
    return Partner.objects.create(
        name="Acme Corp",
        partner_type=PartnerType.COMPANY,
        is_company=True,
        country=country,
        email="info@acme.com",
    )


@pytest.mark.django_db
class TestPartner:
    def test_create_company_partner(self, acme):
        assert acme.pk is not None
        assert acme.is_company is True
        assert str(acme) == "Acme Corp"

    def test_create_individual_partner(self, acme, country):
        person = Partner.objects.create(
            name="John Doe",
            partner_type=PartnerType.INDIVIDUAL,
            is_company=False,
            parent=acme,
            country=country,
        )
        assert person.parent == acme

    def test_commercial_partner_is_self_when_is_company(self, acme):
        assert acme.commercial_partner == acme

    def test_commercial_partner_climbs_to_company(self, acme, country):
        contact = Partner.objects.create(
            name="Jane Smith",
            partner_type=PartnerType.INDIVIDUAL,
            is_company=False,
            parent=acme,
            country=country,
        )
        assert contact.commercial_partner == acme

    def test_commercial_partner_is_self_when_no_parent(self, country):
        solo = Partner.objects.create(
            name="Solo Person",
            partner_type=PartnerType.INDIVIDUAL,
            is_company=False,
            country=country,
        )
        assert solo.commercial_partner == solo

    def test_soft_delete_hides_partner(self, acme):
        acme.delete()
        assert not Partner.objects.filter(pk=acme.pk).exists()
        assert Partner.all_objects.filter(pk=acme.pk).exists()

    def test_restore_makes_visible_again(self, acme):
        acme.delete()
        acme.restore()
        assert Partner.objects.filter(pk=acme.pk).exists()

    def test_address_fields_stored(self, acme, country):
        acme.street = "42 Innovation Ave"
        acme.city = "Tech City"
        acme.zip_code = "90001"
        acme.country = country
        acme.save()
        refreshed = Partner.objects.get(pk=acme.pk)
        assert refreshed.street == "42 Innovation Ave"

    def test_vat_and_ref_stored(self, acme):
        acme.vat = "US123456789"
        acme.ref = "CUST-001"
        acme.save()
        refreshed = Partner.objects.get(pk=acme.pk)
        assert refreshed.vat == "US123456789"
        assert refreshed.ref == "CUST-001"


@pytest.mark.django_db
class TestPartnerTag:
    def test_create_tag(self):
        tag = PartnerTag.objects.create(name="VIP", color="gold")
        assert str(tag) == "VIP"

    def test_assign_tag_to_partner(self, acme):
        tag = PartnerTag.objects.create(name="Priority")
        acme.tags.add(tag)
        assert acme.tags.filter(name="Priority").exists()

    def test_multiple_tags(self, acme):
        t1 = PartnerTag.objects.create(name="Premium")
        t2 = PartnerTag.objects.create(name="Global")
        acme.tags.set([t1, t2])
        assert acme.tags.count() == 2


# ---------------------------------------------------------------------------
# Materialized path tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestPartnerMaterializedPath:
    def test_root_path_is_pk_hex(self, acme):
        assert acme.path == acme.pk.hex

    def test_child_path_includes_parent(self, acme, country):
        child = Partner.objects.create(name="Child Co", is_company=True, parent=acme, country=country)
        assert child.path == f"{acme.pk.hex}/{child.pk.hex}"

    def test_grandchild_path_includes_full_ancestry(self, acme, country):
        child = Partner.objects.create(name="Child Co", is_company=True, parent=acme, country=country)
        grandchild = Partner.objects.create(name="Grandchild", parent=child, country=country)
        assert grandchild.path == f"{acme.pk.hex}/{child.pk.hex}/{grandchild.pk.hex}"

    def test_depth_root_is_zero(self, acme):
        assert acme.depth == 0

    def test_depth_child_is_one(self, acme, country):
        child = Partner.objects.create(name="Child", parent=acme, country=country)
        assert child.depth == 1

    def test_depth_grandchild_is_two(self, acme, country):
        child = Partner.objects.create(name="Child", is_company=True, parent=acme, country=country)
        grandchild = Partner.objects.create(name="Grandchild", parent=child, country=country)
        assert grandchild.depth == 2

    def test_get_descendants_returns_all_below(self, acme, country):
        child = Partner.objects.create(name="Child", is_company=True, parent=acme, country=country)
        grandchild = Partner.objects.create(name="Grandchild", parent=child, country=country)

        descendants = acme.get_descendants()
        pks = {p.pk for p in descendants}
        assert child.pk in pks
        assert grandchild.pk in pks
        assert acme.pk not in pks

    def test_get_descendants_child_excludes_sibling(self, acme, country):
        child_a = Partner.objects.create(name="Child A", is_company=True, parent=acme, country=country)
        child_b = Partner.objects.create(name="Child B", is_company=True, parent=acme, country=country)
        grandchild = Partner.objects.create(name="Grandchild", parent=child_a, country=country)

        desc_of_a = {p.pk for p in child_a.get_descendants()}
        assert grandchild.pk in desc_of_a
        assert child_b.pk not in desc_of_a

    def test_get_ancestors_returns_ordered_root_first(self, acme, country):
        child = Partner.objects.create(name="Child", is_company=True, parent=acme, country=country)
        grandchild = Partner.objects.create(name="Grandchild", parent=child, country=country)

        ancestors = grandchild.get_ancestors()
        assert len(ancestors) == 2
        assert ancestors[0].pk == acme.pk        # root first
        assert ancestors[1].pk == child.pk       # then immediate parent

    def test_get_ancestors_root_returns_empty_list(self, acme):
        assert acme.get_ancestors() == []

    def test_get_children_returns_direct_only(self, acme, country):
        child = Partner.objects.create(name="Child", is_company=True, parent=acme, country=country)
        Partner.objects.create(name="Grandchild", parent=child, country=country)

        children = list(acme.get_children())
        assert len(children) == 1
        assert children[0].pk == child.pk

    def test_reparent_updates_own_path(self, acme, country):
        other_root = Partner.objects.create(name="Other Corp", is_company=True, country=country)
        child = Partner.objects.create(name="Child", is_company=True, parent=acme, country=country)

        # Move child from Acme to other_root
        child.parent = other_root
        child.save()

        child.refresh_from_db()
        assert child.path == f"{other_root.pk.hex}/{child.pk.hex}"

    def test_reparent_cascades_to_descendants(self, acme, country):
        other_root = Partner.objects.create(name="Other Corp", is_company=True, country=country)
        child = Partner.objects.create(name="Child", is_company=True, parent=acme, country=country)
        grandchild = Partner.objects.create(name="Grandchild", parent=child, country=country)

        # Reparent child → other_root
        child.parent = other_root
        child.save()

        grandchild.refresh_from_db()
        expected = f"{other_root.pk.hex}/{child.pk.hex}/{grandchild.pk.hex}"
        assert grandchild.path == expected

    def test_move_to_root_removes_parent_prefix(self, acme, country):
        child = Partner.objects.create(name="Child", is_company=True, parent=acme, country=country)

        child.parent = None
        child.save()

        child.refresh_from_db()
        assert child.path == child.pk.hex


@pytest.mark.django_db
class TestPartnerDisplayName:
    def test_display_name_company_is_just_name(self, acme):
        assert acme.display_name == "Acme Corp"

    def test_display_name_contact_includes_company(self, acme, country):
        contact = Partner.objects.create(
            name="John Doe",
            is_company=False,
            parent=acme,
            country=country,
        )
        assert contact.display_name == "Acme Corp, John Doe"

    def test_display_name_sub_company_is_just_name(self, acme, country):
        sub = Partner.objects.create(
            name="Acme UK",
            is_company=True,
            parent=acme,
            country=country,
        )
        assert sub.display_name == "Acme UK"
