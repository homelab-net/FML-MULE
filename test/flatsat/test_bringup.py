"""Tests for `mule.bringup`.

The point of the module is that a wrong order fails here rather than on a node,
where it presents as a radio fault. So most of these plant a specific wrong
order and assert the rule that catches it, in the same spirit as the planted
violations in `test/unit/validate_docs.bats`.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from mule.bringup import (
    BATMAN_HARD_MTU_BYTES,
    REQUIRED_ORDER,
    Step,
    state_violations,
    violations,
)

from .fakes import FakeMeshState

#: A sound sequence. Every other case in this file is this one, damaged.
GOOD: tuple[Step, ...] = (
    "driver_loaded",
    "link_up",
    "associated",
    "routing_algo_set",
    "hard_mtu_set",
    "mesh_interface_created",
    "mesh_member_added",
    "mesh_interface_up",
    "services_started",
)


def test_a_sound_sequence_breaks_nothing() -> None:
    """Accept the order the template and the probe between them establish."""
    assert violations(GOOD) == []


def test_the_mtu_and_the_algorithm_may_be_set_in_either_order() -> None:
    """Permit what no evidence orders.

    Both are established to come before the add. Nothing establishes an order
    between them, so enforcing one would be inventing a constraint.
    """
    swapped = list(GOOD)
    i, j = swapped.index("routing_algo_set"), swapped.index("hard_mtu_set")
    swapped[i], swapped[j] = swapped[j], swapped[i]

    assert violations(swapped) == []


def test_an_empty_sequence_breaks_nothing() -> None:
    """Report nothing for a node that has not started.

    A rule is about a step that happened. None have.
    """
    assert violations([]) == []


@pytest.mark.parametrize(
    ("earlier", "later"),
    REQUIRED_ORDER,
    ids=[f"{a}-before-{b}" for a, b in REQUIRED_ORDER],
)
def test_every_rule_is_caught_when_the_steps_are_swapped(
    earlier: Step, later: Step
) -> None:
    """Catch each rule in turn, by performing its two steps the wrong way round.

    Parametrised over the rules themselves rather than written out, so a rule
    added to REQUIRED_ORDER without a test is impossible: the case appears with
    the rule.
    """
    swapped = list(GOOD)
    i, j = swapped.index(earlier), swapped.index(later)
    swapped[i], swapped[j] = swapped[j], swapped[i]

    assert (earlier, later) in violations(swapped)


@pytest.mark.parametrize(
    ("earlier", "later"),
    REQUIRED_ORDER,
    ids=[f"{a}-missing-before-{b}" for a, b in REQUIRED_ORDER],
)
def test_a_prerequisite_that_never_happened_is_a_violation(
    earlier: Step, later: Step
) -> None:
    """Fail a step whose prerequisite was skipped, not just one done late.

    Adding an interface to the mesh with the routing algorithm never set is not
    an untidy sequence. batman-adv fixes the algorithm at the moment of the
    add, so the node comes up on whatever the default was and looks correct.
    """
    without = [step for step in GOOD if step != earlier]

    assert (earlier, later) in violations(without)


def test_the_algorithm_set_after_the_interface_exists_is_caught() -> None:
    """Catch the algorithm set too late, where too late is earlier than it looks.

    `systemd.netdev(5)`: "The algorithm cannot be changed after interface
    creation." So the deadline is creation, not the first member add. This
    sequence sets it after creation but BEFORE any member is added, which the
    earlier version of `REQUIRED_ORDER` accepted and which still leaves the
    node running the wrong algorithm.
    """
    late = (
        "driver_loaded",
        "link_up",
        "associated",
        "hard_mtu_set",
        "mesh_interface_created",
        "routing_algo_set",
        "mesh_member_added",
        "mesh_interface_up",
        "services_started",
    )

    assert ("routing_algo_set", "mesh_interface_created") in violations(late)


def test_an_unassociated_member_is_not_a_violation() -> None:
    """Permit what the mesh probe actually does.

    `.github/workflows/mesh-probe.yml` attaches `veth` interfaces that
    associate with nothing, and the mesh forms. An earlier version required
    `associated` before `mesh_member_added`, which made this repository's own
    working probe a violation.
    """
    wired = (
        "driver_loaded",
        "link_up",
        "routing_algo_set",
        "hard_mtu_set",
        "mesh_interface_created",
        "mesh_member_added",
        "mesh_interface_up",
        "services_started",
    )

    assert violations(wired) == []


def test_a_reversed_sequence_reports_every_rule() -> None:
    """Report all of them, not the first.

    A caller diagnosing a node needs the whole picture; returning on the first
    broken rule would hide the rest behind it.
    """
    assert len(violations(tuple(reversed(GOOD)))) == len(REQUIRED_ORDER)


# --- the finished node, rather than the sequence -----------------------------
#
# state_violations answers a different question from violations, and the tests
# below exist as much to pin down what it CANNOT answer as what it can.

#: A node that came up correctly.
SOUND = FakeMeshState(
    algo="BATMAN_IV",
    bla=False,
    mtu_bytes=BATMAN_HARD_MTU_BYTES,
    members=1,
)


def test_a_sound_node_breaks_no_invariant() -> None:
    """Accept a node that holds all of them."""
    assert state_violations(SOUND, "BATMAN_IV") == []


def test_a_mesh_running_the_wrong_algorithm_is_caught() -> None:
    """Catch the trace a late routing algorithm leaves.

    batman-adv fixes the algorithm when the interface is added, so a mesh
    running something other than the intended algorithm is evidence the
    algorithm was set after the add, or never. FML-ADR-053 chose BATMAN-IV
    deliberately and a node quietly running BATMAN_V has undone that.
    """
    observed = replace(SOUND, algo="BATMAN_V")

    broken = state_violations(observed, "BATMAN_IV")

    assert broken == ["routing_algo_not_the_intended_one"]


def test_bridge_loop_avoidance_left_on_is_caught() -> None:
    """Catch FML-ADR-056 not being in force, whatever the configuration says."""
    observed = replace(SOUND, bla=True)

    broken = state_violations(observed, "BATMAN_IV")

    assert "bridge_loop_avoidance_enabled_on_the_mesh" in broken


def test_a_hard_interface_below_the_batman_minimum_is_caught() -> None:
    """Catch an MTU that makes every full-size frame fragment."""
    observed = replace(SOUND, mtu_bytes=1500)

    assert "hard_mtu_below_batman_minimum" in state_violations(observed, "BATMAN_IV")


def test_a_mesh_with_nothing_attached_is_caught() -> None:
    """Catch the shape a node has when the add failed.

    Attaching an interface that is not up is what produces it, and it is the
    failure the ordering rules exist to prevent.
    """
    observed = replace(SOUND, members=0)

    assert "mesh_has_no_members" in state_violations(observed, "BATMAN_IV")


@pytest.mark.parametrize(
    "field",
    ["algo", "bla", "mtu_bytes", "members"],
)
def test_a_reading_the_platform_cannot_answer_is_not_a_violation(field: str) -> None:
    """Report nothing for a reading that came back None.

    The platform saying it cannot answer is a different thing from the platform
    saying the invariant is broken. Treating them alike is how a node with no
    instrumentation comes to look faulty, which is the failure AGENTS.md
    records four times over.
    """
    observed = replace(SOUND, **{field: None})

    assert state_violations(observed, "BATMAN_IV") == []


def test_a_late_mtu_leaves_no_trace_and_is_not_caught() -> None:
    """Pin down what this cannot do, so nobody reads it as an order check.

    An MTU raised after the interface was added ends with the hard interface at
    the right value. The snapshot sees the value, not when it was set, so this
    node passes while having been brought up in the wrong order. Only a
    recorded sequence catches that, which is what `violations` is for.

    This test exists to fail if someone later claims state_violations verifies
    ordering. It does not.
    """
    late_but_now_correct = SOUND

    assert state_violations(late_but_now_correct, "BATMAN_IV") == []
    assert violations(["mesh_member_added", "hard_mtu_set"]) != []
