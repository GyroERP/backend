"""Tests for Sequence and SequenceDateRange models."""

from datetime import date

import pytest

from gyrokernel.models import Sequence, SequenceDateRange, SequenceImplementation


@pytest.fixture
def basic_seq(db):
    return Sequence.objects.create(
        name="Invoice", code="INV",
        prefix="INV/", padding=4, step=1,
        implementation=SequenceImplementation.STANDARD,
    )


@pytest.fixture
def dated_seq(db):
    return Sequence.objects.create(
        name="Dated Invoice", code="DINV",
        prefix="INV/{year}/{month}/", padding=4, step=1,
        implementation=SequenceImplementation.NO_GAP,
        use_date_range=True,
    )


@pytest.mark.django_db
class TestSequenceBasic:
    def test_next_by_code_returns_formatted_string(self, basic_seq):
        result = Sequence.next_by_code("INV")
        assert result == "INV/0001"

    def test_next_by_code_increments(self, basic_seq):
        first = Sequence.next_by_code("INV")
        second = Sequence.next_by_code("INV")
        assert first == "INV/0001"
        assert second == "INV/0002"

    def test_padding_applied(self, db):
        Sequence.objects.create(
            name="Wide", code="WIDE", prefix="W-", padding=6, step=1,
            implementation=SequenceImplementation.STANDARD,
        )
        result = Sequence.next_by_code("WIDE")
        assert result == "W-000001"

    def test_step_increments_by_step(self, db):
        Sequence.objects.create(
            name="Step5", code="STEP5", prefix="S-", padding=3, step=5,
            implementation=SequenceImplementation.STANDARD,
        )
        first = Sequence.next_by_code("STEP5")
        second = Sequence.next_by_code("STEP5")
        assert first == "S-001"
        assert second == "S-006"

    def test_nonexistent_code_raises(self):
        with pytest.raises(ValueError, match="No active sequence"):
            Sequence.next_by_code("DOES_NOT_EXIST")

    def test_inactive_sequence_not_found(self, db):
        Sequence.objects.create(
            name="Dead", code="DEAD", prefix="D-", padding=4,
            is_active=False,
        )
        with pytest.raises(ValueError, match="No active sequence"):
            Sequence.next_by_code("DEAD")

    def test_str_representation(self, basic_seq):
        assert str(basic_seq) == "Invoice (INV)"


@pytest.mark.django_db
class TestSequenceDateRange:
    def test_prefix_interpolation_year_month(self, dated_seq):
        result = Sequence.next_by_code("DINV", date=date(2024, 6, 15))
        assert result == "INV/2024/06/0001"

    def test_yearly_reset(self, dated_seq):
        first = Sequence.next_by_code("DINV", date=date(2024, 3, 1))
        second = Sequence.next_by_code("DINV", date=date(2024, 3, 15))
        new_year = Sequence.next_by_code("DINV", date=date(2025, 1, 5))

        assert first == "INV/2024/03/0001"
        assert second == "INV/2024/03/0002"
        assert new_year == "INV/2025/01/0001"

    def test_date_range_record_created(self, dated_seq):
        Sequence.next_by_code("DINV", date=date(2024, 1, 1))
        assert SequenceDateRange.objects.filter(
            sequence=dated_seq,
            date_from=date(2024, 1, 1),
        ).exists()

    def test_day_interpolation(self, db):
        Sequence.objects.create(
            name="Daily", code="DAILY",
            prefix="{year}-{month}-{day}-",
            padding=3, step=1,
            implementation=SequenceImplementation.STANDARD,
        )
        result = Sequence.next_by_code("DAILY", date=date(2024, 12, 25))
        assert result == "2024-12-25-001"
