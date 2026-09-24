"""Unit tests for the operating-mode axes.

`mule/modes.py` implements `CCR-01` part A: the thirteen CONOPS section 50
modes are nine concurrent axes rather than one exclusive set.

Two disciplines run through every test here.

**The fake never names a rung.** `FakeRadio` scripts which bearers are present
and which have linked, and nothing else. If it could be told "you are
LOW-BANDWIDTH" the ladder tests would assert that a fixture agrees with itself,
which is exactly how the time tests failed before `FML-ADR-051`.

**Undetermined is not nominal.** Every axis that can be undetermined is tested
for the difference, because collapsing the two is the defect this repository has
now shipped four times.
"""

from __future__ import annotations

import pytest

from mule.bearers import Bearer
from mule.modes import CAPABILITY_LADDER, ModeAssessment, ModeInputs, assess
from mule.power import PowerModel
from mule.power import assess as assess_power

from .conftest import FIXTURE_POWER_MODEL
from .fakes import FakePower, FakeRadio

#: A runtime threshold for the energy axis. Invented, like every number in this
#: directory; TBR-PWR-01 owns the real one. It exists so the axis has something
#: to compare against, and no node is ever configured from it.
FIXTURE_ECONOMY_BELOW_MINUTES = 90

#: A charge high enough that the fixture model projects runtime above the
#: threshold above, and one low enough that it does not. Both are derived by
#: running the model rather than asserted, so neither restates its arithmetic.
FULL_CHARGE = 1.0
LOW_CHARGE = 0.2


def _inputs(
    *,
    present: list[Bearer] | None = None,
    linked: list[Bearer] | None = None,
    hosting: bool = False,
    wan: bool | None = None,
    charge: float | None = None,
    model: PowerModel | None = None,
    peer_reachable: bool | None = True,
) -> ModeInputs:
    """Build mode inputs from scripted readings, never from named outcomes."""
    radio = FakeRadio(
        present=present if present is not None else ["wifi_ap"],
        linked=linked if linked is not None else ["wifi_ap"],
    )
    enumerated = tuple(radio.enumerated())
    return ModeInputs(
        environment="LAB",
        enumerated=enumerated,
        # Read back through the fake's own interface rather than its field, so
        # the test asks the radio what has linked in the same way the node does.
        associated=tuple(b for b in enumerated if radio.associated(b)),
        hosting_shared_services=hosting,
        wan_reachable=wan,
        peer_reachable=peer_reachable,
        power=assess_power(
            # A pack is fitted throughout. Whether an unfitted pack can be
            # reasoned about is mule/power.py's question, not this module's.
            FakePower(pack=True, charge=charge),
            model,
            hosting_shared_services=hosting,
        ),
        lifecycle="OPERATIONAL",
        emission="NORMAL-EMISSION",
        data_marking="LIVE",
    )


def _assess(
    *,
    present: list[Bearer] | None = None,
    linked: list[Bearer] | None = None,
    hosting: bool = False,
    wan: bool | None = None,
    peer_reachable: bool | None = True,
) -> ModeAssessment:
    """Assess with no economy threshold, which is the programme's state today."""
    return assess(
        _inputs(
            present=present,
            linked=linked,
            hosting=hosting,
            wan=wan,
            peer_reachable=peer_reachable,
        ),
        economy_below_minutes=None,
    )


# --- the capability ladder -------------------------------------------------


@pytest.mark.parametrize(("bearer", "rung"), CAPABILITY_LADDER)
def test_the_highest_linked_bearer_sets_the_rung(bearer: Bearer, rung: str) -> None:
    """Each ladder entry is reachable, and reached by its own bearer linking.

    Parametrised over the ladder itself rather than over a written-out copy of
    it. A test listing the pairs again would pass while the ladder said
    something different, which proves only that two literals match.
    """
    result = _assess(present=["wifi_ap", bearer], linked=["wifi_ap", bearer])

    assert result.bearer_capability == rung


def test_a_node_with_only_an_access_point_is_isolated() -> None:
    """CONOPS section 50.9: local EUD and node capability only.

    The access point is serving, so the node is not broken. It has simply no
    way to reach another node, which is the bottom rung a node can report.
    """
    result = _assess(present=["wifi_ap"], linked=["wifi_ap"])

    assert result.bearer_capability == "ISOLATED"
    assert result.degraded_bearer


def test_a_fitted_bearer_that_has_not_linked_does_not_raise_the_rung() -> None:
    """Fitment is not capability.

    A node carrying a mesh radio that never associated has the same reach as a
    node without one. Counting hardware rather than links would report the
    healthiest configuration the node might have had.
    """
    result = _assess(present=["wifi_ap", "wifi_mesh", "lora"], linked=["wifi_ap"])

    assert result.bearer_capability == "ISOLATED"


def test_the_rung_follows_the_best_link_not_the_worst() -> None:
    """A node linked on mesh and LoRa is at the mesh rung.

    The ladder is ordered by capability, and a node uses the best bearer it
    has. Reporting the worst would put a fully connected node on the LoRa rung.
    """
    result = _assess(
        present=["wifi_ap", "wifi_mesh", "lora"],
        linked=["wifi_ap", "wifi_mesh", "lora"],
    )

    assert result.bearer_capability == "NOMINAL-IP"
    assert not result.degraded_bearer


# --- deployment context ----------------------------------------------------


def test_a_node_with_a_linked_inter_node_bearer_is_networked() -> None:
    """NETWORKED means meshed with another node, which needs a formed link."""
    result = _assess(present=["wifi_ap", "wifi_mesh"], linked=["wifi_ap", "wifi_mesh"])

    assert result.deployment == "NETWORKED"


def test_lora_alone_does_not_make_a_node_networked() -> None:
    """LoRa is a separate non-IP plane, `FML-ADR-026`, not the mesh.

    It is on the capability ladder because it carries traffic between nodes,
    and it is not an inter-node bearer for deployment purposes because it is
    not bridged into the mesh. Conflating the two would report a LoRa-only node
    as networked when nothing IP reaches a peer.
    """
    result = _assess(present=["wifi_ap", "lora"], linked=["wifi_ap", "lora"])

    assert result.deployment == "STANDALONE"
    assert result.bearer_capability == "LOW-BANDWIDTH"


def test_an_unlinked_mesh_radio_leaves_the_node_standalone() -> None:
    """Fitted and not linked is not networked, for the same reason as the rung."""
    result = _assess(present=["wifi_ap", "wifi_mesh"], linked=["wifi_ap"])

    assert result.deployment == "STANDALONE"


# --- what the node cannot determine ---------------------------------------


def test_a_node_not_hosting_cannot_say_whether_a_peer_is() -> None:
    """SERVERLESS-TAK is a claim about the whole mesh, not about this node.

    Answering it needs the Service Authority Registry, which `FML-ADR-049`
    folds into the blocked status aggregator. Reporting SERVERLESS-TAK from a
    node that simply is not hosting would be wrong on any mesh where a peer is.
    """
    result = _assess(hosting=False)

    assert result.shared_tak is None
    reasons = dict(result.undetermined)
    assert "TBR-TAK-01" in reasons["shared_tak"]


def test_a_hosting_node_is_server_enhanced() -> None:
    """A node running the service knows the service is reachable."""
    result = _assess(hosting=True)

    assert result.shared_tak == "SERVER-ENHANCED"
    assert "shared_tak" not in dict(result.undetermined)


def test_no_wan_report_is_undetermined_rather_than_no_wan() -> None:
    """Nothing reporting is not the same as reporting nothing reachable.

    `NO-WAN` says a gateway was looked for and not found. Today nothing looks,
    and saying `NO-WAN` would be a finding the node never made.
    """
    result = _assess(wan=None)

    assert result.wan is None
    assert "wan" in dict(result.undetermined)


@pytest.mark.parametrize(
    ("reachable", "expected"), [(True, "WAN-ENHANCED"), (False, "NO-WAN")]
)
def test_a_reported_wan_reachability_is_carried(reachable: bool, expected: str) -> None:
    """Both determined values are reachable once something reports."""
    result = _assess(wan=reachable)

    assert result.wan == expected
    assert "wan" not in dict(result.undetermined)


# --- the energy axis needs both a model and a threshold --------------------


def test_with_no_power_model_the_energy_axis_is_undetermined() -> None:
    """A node that cannot project runtime cannot say it is comfortable.

    This is the failure shape that has recurred four times: a default healthy
    answer where the honest answer is that nobody has measured anything.
    """
    result = assess(_inputs(charge=FULL_CHARGE), economy_below_minutes=None)

    assert result.energy is None
    assert "TBR-PWR-01" in dict(result.undetermined)["energy"]


def test_with_a_model_but_no_threshold_the_energy_axis_is_undetermined() -> None:
    """Knowing the runtime is not knowing when it becomes a problem.

    The threshold is `TBR-PWR-01`'s, and a node holding a runtime estimate
    against no threshold has nothing to compare.
    """
    result = assess(
        _inputs(charge=FULL_CHARGE, model=FIXTURE_POWER_MODEL),
        economy_below_minutes=None,
    )

    assert result.energy is None
    assert "TBR-PWR-01" in dict(result.undetermined)["energy"]


def test_ample_runtime_is_nominal_and_short_runtime_sheds_load() -> None:
    """Both energy values are reachable, and the threshold is what separates them.

    The two charges are not asserted to produce particular runtimes. The model
    is run to find what it projects, and the test checks only that the axis
    follows the comparison against the threshold. Asserting the minutes would
    restate the arithmetic in `mule/power.py`.
    """
    ample = _inputs(charge=FULL_CHARGE, model=FIXTURE_POWER_MODEL)
    scarce = _inputs(charge=LOW_CHARGE, model=FIXTURE_POWER_MODEL)

    ample_minutes = ample.power.projected_runtime_minutes
    scarce_minutes = scarce.power.projected_runtime_minutes
    assert ample_minutes is not None and scarce_minutes is not None
    assert scarce_minutes < FIXTURE_ECONOMY_BELOW_MINUTES <= ample_minutes, (
        "the fixture charges no longer straddle the threshold; pick new ones"
    )

    assert (
        assess(ample, economy_below_minutes=FIXTURE_ECONOMY_BELOW_MINUTES).energy
        == "NOMINAL-ENERGY"
    )
    assert (
        assess(scarce, economy_below_minutes=FIXTURE_ECONOMY_BELOW_MINUTES).energy
        == "FIELD-ECONOMY"
    )


# --- the axes the node is told --------------------------------------------


def test_the_commanded_axes_are_carried_not_decided() -> None:
    """Environment, lifecycle, emission and data marking are authorized action.

    `CCR-01` part B would make that binding. A node cannot observe that it is
    on a bench, being carried, or running an exercise, and deriving any of them
    would be inventing a reading.
    """
    inputs = ModeInputs(
        environment="FIELD",
        enumerated=("wifi_ap",),
        associated=("wifi_ap",),
        hosting_shared_services=False,
        wan_reachable=None,
        peer_reachable=True,
        power=assess_power(FakePower(), None, hosting_shared_services=False),
        lifecycle="TRANSPORT-SECURE",
        emission="EMCON-SILENT",
        data_marking="EXERCISE",
    )

    result = assess(inputs, economy_below_minutes=None)

    assert result.environment == "FIELD"
    assert result.lifecycle == "TRANSPORT-SECURE"
    assert result.emission == "EMCON-SILENT"
    assert result.data_marking == "EXERCISE"


def test_axes_hold_at_once() -> None:
    """The point of `CCR-01` part A: these are not alternatives.

    A node on a bench, running an exercise, silent, and down to LoRa is in all
    four states simultaneously. An exclusive taxonomy would have to discard
    three of them, and section 51 requires exactly this combination by letting
    exercise control force a degradation state.
    """
    inputs = ModeInputs(
        environment="LAB",
        enumerated=("wifi_ap", "lora"),
        associated=("wifi_ap", "lora"),
        hosting_shared_services=False,
        wan_reachable=None,
        peer_reachable=True,
        power=assess_power(FakePower(), None, hosting_shared_services=False),
        lifecycle="OPERATIONAL",
        emission="EMCON-SILENT",
        data_marking="EXERCISE",
    )

    result = assess(inputs, economy_below_minutes=None)

    assert result.environment == "LAB"
    assert result.emission == "EMCON-SILENT"
    assert result.data_marking == "EXERCISE"
    assert result.bearer_capability == "LOW-BANDWIDTH"


# --- association is not capability -----------------------------------------


def test_a_node_reaching_no_peer_is_isolated_whatever_has_linked() -> None:
    """The defect the mesh probe measured, in one assertion.

    A freshly formed batman-adv mesh converges its originator table in about
    four seconds and cannot carry client traffic for roughly twenty-five more.
    For that window every bearer is associated and the node reaches nobody.
    Reporting NOMINAL-IP there is a claim to carry traffic the node cannot
    carry, and an operator acting on it would wait on a link that is not there.
    """
    result = _assess(
        present=["wifi_ap", "wifi_mesh"],
        linked=["wifi_ap", "wifi_mesh"],
        peer_reachable=False,
    )

    assert result.bearer_capability == "ISOLATED"
    assert result.degraded_bearer


def test_an_unmeasured_peer_does_not_downgrade_but_is_recorded() -> None:
    """`None` is not `False`, and the difference decides the rung.

    Nothing on a real node probes peer reachability yet. Downgrading on an
    absent measurement would report ISOLATED for every node that has no probe,
    which is its own false claim in the other direction. The rung stays at the
    ceiling association allows and the gap is recorded, so a caller can tell
    "reaches peers" from "nobody asked".
    """
    result = _assess(
        present=["wifi_ap", "wifi_mesh"],
        linked=["wifi_ap", "wifi_mesh"],
        peer_reachable=None,
    )

    assert result.bearer_capability == "NOMINAL-IP"
    reasons = dict(result.undetermined)
    assert "ceiling" in reasons["bearer_capability"]


def test_a_reachable_peer_leaves_the_ladder_alone() -> None:
    """The other half. A check that only fires one way has not been tested."""
    result = _assess(
        present=["wifi_ap", "wifi_mesh"],
        linked=["wifi_ap", "wifi_mesh"],
        peer_reachable=True,
    )

    assert result.bearer_capability == "NOMINAL-IP"
    assert "bearer_capability" not in dict(result.undetermined)


def test_a_node_with_no_bearer_linked_records_no_reachability_gap() -> None:
    """An access-point-only node is ISOLATED by association, not by silence.

    Recording an undetermined reachability for a node that has linked nothing
    would attach a caveat to a rung that association already settles.
    """
    result = _assess(present=["wifi_ap"], linked=["wifi_ap"], peer_reachable=None)

    assert result.bearer_capability == "ISOLATED"
    assert "bearer_capability" not in dict(result.undetermined)
