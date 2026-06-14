"""Tests for DomainEvaluator — JSON domain to Django Q conversion."""

import pytest
from django.db.models import Q

from gyrokernel.domain import DomainError, DomainEvaluator


@pytest.fixture
def ev():
    return DomainEvaluator()


class TestDomainEvaluatorBasicOps:
    def test_empty_domain_returns_empty_q(self, ev):
        q = ev.to_q([])
        assert q == Q()

    def test_equals(self, ev):
        q = ev.to_q([["name", "=", "Alice"]])
        assert q == Q(name="Alice")

    def test_not_equals(self, ev):
        q = ev.to_q([["status", "!=", "inactive"]])
        assert q == ~Q(status="inactive")

    def test_less_than(self, ev):
        q = ev.to_q([["age", "<", 30]])
        assert q == Q(age__lt=30)

    def test_less_than_or_equal(self, ev):
        q = ev.to_q([["age", "<=", 30]])
        assert q == Q(age__lte=30)

    def test_greater_than(self, ev):
        q = ev.to_q([["score", ">", 100]])
        assert q == Q(score__gt=100)

    def test_greater_than_or_equal(self, ev):
        q = ev.to_q([["score", ">=", 100]])
        assert q == Q(score__gte=100)

    def test_in_operator(self, ev):
        q = ev.to_q([["status", "in", ["active", "pending"]]])
        assert q == Q(status__in=["active", "pending"])

    def test_not_in_operator(self, ev):
        q = ev.to_q([["status", "not in", ["deleted", "archived"]]])
        assert q == ~Q(status__in=["deleted", "archived"])

    def test_like_operator(self, ev):
        q = ev.to_q([["name", "like", "acme"]])
        assert q == Q(name__icontains="acme")

    def test_ilike_operator(self, ev):
        q = ev.to_q([["name", "ilike", "ACME"]])
        assert q == Q(name__icontains="ACME")

    def test_multiple_conditions_are_anded(self, ev):
        q = ev.to_q([
            ["is_active", "=", True],
            ["partner_type", "=", "company"],
        ])
        expected = Q(is_active=True) & Q(partner_type="company")
        assert q == expected

    def test_dot_field_converts_to_dunder(self, ev):
        q = ev.to_q([["country.code", "=", "US"]])
        assert q == Q(country__code="US")


class TestDomainEvaluatorContextVars:
    def test_at_variable_resolved_from_context(self, ev):
        q = ev.to_q(
            [["company_id", "=", "@company_id"]],
            context={"company_id": "abc-123"},
        )
        assert q == Q(company_id="abc-123")

    def test_at_variable_list_in_context(self, ev):
        q = ev.to_q(
            [["company_id", "in", "@company_ids"]],
            context={"company_ids": ["id1", "id2"]},
        )
        assert q == Q(company_id__in=["id1", "id2"])

    def test_missing_context_variable_raises(self, ev):
        with pytest.raises(DomainError, match="@user_id"):
            ev.to_q([["user_id", "=", "@user_id"]], context={})


class TestDomainEvaluatorErrors:
    def test_non_list_domain_raises(self, ev):
        with pytest.raises(DomainError):
            ev.to_q("not a list")

    def test_condition_not_triple_raises(self, ev):
        with pytest.raises(DomainError):
            ev.to_q([["field", "="]])  # only 2 elements

    def test_unknown_operator_raises(self, ev):
        with pytest.raises(DomainError, match="Unknown domain operator"):
            ev.to_q([["name", "MATCHES", "foo"]])

    def test_in_with_non_list_raises(self, ev):
        with pytest.raises(DomainError, match="requires a list"):
            ev.to_q([["id", "in", "not-a-list"]])

    def test_not_in_with_non_list_raises(self, ev):
        with pytest.raises(DomainError, match="requires a list"):
            ev.to_q([["id", "not in", 42]])

    def test_empty_field_name_raises(self, ev):
        with pytest.raises(DomainError):
            ev.to_q([["", "=", "value"]])
