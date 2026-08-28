"""Unit tests for the runtime estimate.

`mule/power.py` is the procedure CONOPS sections 59 to 61 specify, written
before `TBR-PWR-01` supplies the numbers it consumes. These tests exercise it
both ways: with no model, which is the state of the programme today, and with a
synthetic one, which is the state the day that trade closes.

Every number below comes from `FIXTURE_POWER_MODEL` and is invented. None of it
is evidence about any battery.
"""

from __future__ import annotations

import pytest

from mule.power import PowerModel, assess

from .conftest import FIXTURE_POWER_MODEL
from .fakes import FakePower

FULL = 1.0
HALF = 0.5
FREEZING = -5.0


# --- what the node can say today ------------------------------------------


def test_with_no_model_the_node_refuses_to_estimate() -> None:
    """Today's honest answer, and the reason the module is still worth having.

    The decision path is complete and tested. Only the numbers are absent, and
    the refusal names the trade that will supply them.
    """
    result = assess(
        FakePower(pack=True, charge=FULL), None, hosting_shared_services=False
    )

    assert result.projected_runtime_minutes is None
    assert result.reason is not None
    assert "TBR-PWR-01" in result.reason


def test_no_pack_is_a_different_answer_from_no_model() -> None:
    """Three ways to not know, three distinct reasons.

    An operator acts differently on "no pack fitted", "nobody has measured
    this" and "the pack cannot report its charge". Collapsing them into one
    None would tell nobody anything.
    """
    no_pack = assess(FakePower(pack=False), None, hosting_shared_services=False)
    no_model = assess(
        FakePower(pack=True, charge=FULL), None, hosting_shared_services=False
    )
    no_gauge = assess(
        FakePower(pack=True, charge=None),
        FIXTURE_POWER_MODEL,
        hosting_shared_services=False,
    )

    reasons = {no_pack.reason, no_model.reason, no_gauge.reason}
    assert len(reasons) == 3
    for result in (no_pack, no_model, no_gauge):
        assert result.projected_runtime_minutes is None
    assert "not report its state of charge" in (no_gauge.reason or "")


# --- what it will say once TBR-PWR-01 closes ------------------------------


def test_a_measured_model_produces_an_estimate() -> None:
    """100 Wh, a quarter held in reserve, 12.5 W draw: six hours.

    Asserted against the arithmetic rather than a remembered figure, so that
    changing the fixture changes the expectation.
    """
    model = FIXTURE_POWER_MODEL
    expected = int(
        model.pack_capacity_wh
        * FULL
        * (1.0 - model.reserve_fraction)
        / model.baseline_load_w
        * 60
    )

    result = assess(
        FakePower(pack=True, charge=FULL), model, hosting_shared_services=False
    )

    assert result.projected_runtime_minutes == expected
    assert result.reason is None


def test_hosting_shared_services_shortens_the_estimate() -> None:
    """CONOPS section 60's service-host power penalty, and section 67's question.

    The operator is asked whether hosting is reducing runtime. This is what
    answers it, and the answer has to be derived rather than declared.
    """
    unhosted = assess(
        FakePower(pack=True, charge=FULL),
        FIXTURE_POWER_MODEL,
        hosting_shared_services=False,
    )
    hosted = assess(
        FakePower(pack=True, charge=FULL),
        FIXTURE_POWER_MODEL,
        hosting_shared_services=True,
    )

    assert hosted.projected_runtime_minutes < unhosted.projected_runtime_minutes
    assert hosted.hosting_reduces_runtime is True


def test_a_model_with_no_hosting_penalty_says_hosting_does_not_reduce_runtime() -> None:
    free = PowerModel(
        pack_capacity_wh=FIXTURE_POWER_MODEL.pack_capacity_wh,
        reserve_fraction=FIXTURE_POWER_MODEL.reserve_fraction,
        baseline_load_w=FIXTURE_POWER_MODEL.baseline_load_w,
        hosting_load_w=0.0,
    )

    result = assess(
        FakePower(pack=True, charge=FULL), free, hosting_shared_services=True
    )

    assert result.hosting_reduces_runtime is False


def test_cold_derates_the_estimate() -> None:
    """CONOPS section 61: cold behaviour is first-order, not a footnote.

    The nominal objective is explicitly not winter endurance, so a node that
    reported the same runtime at minus five as at room temperature would be
    telling an operator something the CONOPS forbids assuming.
    """
    warm = assess(
        FakePower(pack=True, charge=FULL, temperature_c=20.0),
        FIXTURE_POWER_MODEL,
        hosting_shared_services=False,
    )
    cold = assess(
        FakePower(pack=True, charge=FULL, temperature_c=FREEZING),
        FIXTURE_POWER_MODEL,
        hosting_shared_services=False,
    )

    assert cold.projected_runtime_minutes < warm.projected_runtime_minutes


def test_an_uninstrumented_pack_gets_no_derating_and_that_is_visible() -> None:
    """Optimistic, deliberately, rather than inventing a penalty.

    The alternative is derating by a factor nobody measured for a temperature
    nobody read. Whether an uninstrumented pack is acceptable belongs to
    TBR-PWR-01 and TBR-THERM-01; this records what the code does meanwhile.
    """
    unknown = assess(
        FakePower(pack=True, charge=FULL, temperature_c=None),
        FIXTURE_POWER_MODEL,
        hosting_shared_services=False,
    )
    warm = assess(
        FakePower(pack=True, charge=FULL, temperature_c=20.0),
        FIXTURE_POWER_MODEL,
        hosting_shared_services=False,
    )

    assert unknown.projected_runtime_minutes == warm.projected_runtime_minutes


@pytest.mark.parametrize("charge", [FULL, HALF, 0.0])
def test_the_estimate_tracks_state_of_charge(charge: float) -> None:
    result = assess(
        FakePower(pack=True, charge=charge),
        FIXTURE_POWER_MODEL,
        hosting_shared_services=False,
    )
    full = assess(
        FakePower(pack=True, charge=FULL),
        FIXTURE_POWER_MODEL,
        hosting_shared_services=False,
    )

    assert result.projected_runtime_minutes == int(
        (full.projected_runtime_minutes or 0) * charge
    )


def test_an_unhealthy_pack_is_reported_even_when_runtime_is_known() -> None:
    result = assess(
        FakePower(pack=True, healthy=False, charge=FULL),
        FIXTURE_POWER_MODEL,
        hosting_shared_services=False,
    )

    assert result.pack_unhealthy
    assert result.projected_runtime_minutes is not None


def test_a_model_claiming_no_load_is_refused_rather_than_divided_by() -> None:
    """A node that draws nothing would run forever, which is not a result.

    Without this the estimate divides by zero. Refusing is right: a measured
    model reporting no load means the measurement is wrong, and the operator
    should be told the node cannot say rather than handed an infinity.
    """
    impossible = PowerModel(
        pack_capacity_wh=FIXTURE_POWER_MODEL.pack_capacity_wh,
        reserve_fraction=FIXTURE_POWER_MODEL.reserve_fraction,
        baseline_load_w=0.0,
        hosting_load_w=0.0,
    )

    result = assess(
        FakePower(pack=True, charge=FULL), impossible, hosting_shared_services=False
    )

    assert result.projected_runtime_minutes is None
    assert result.reason is not None
    assert "no load" in result.reason
