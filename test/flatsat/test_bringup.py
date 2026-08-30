"""Tests for `mule.bringup`.

The point of the module is that a wrong order fails here rather than on a node,
where it presents as a radio fault. So most of these plant a specific wrong
order and assert the rule that catches it, in the same spirit as the planted
violations in `test/unit/validate_docs.bats`.
"""

from __future__ import annotations

import pytest

from mule.bringup import REQUIRED_ORDER, Step, violations

#: A sound sequence. Every other case in this file is this one, damaged.
GOOD: tuple[Step, ...] = (
    "driver_loaded",
    "link_up",
    "associated",
    "routing_algo_set",
    "hard_mtu_set",
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


def test_the_algorithm_set_after_the_add_is_caught() -> None:
    """Catch the specific failure the mesh probe had to discover.

    Named on its own rather than left to the parametrised cases because it is
    the one that cost a run: the algorithm is fixed for an interface when the
    interface is added, so setting it afterwards changes nothing while reading
    exactly like a node that had been configured.
    """
    late = (
        "driver_loaded",
        "link_up",
        "associated",
        "hard_mtu_set",
        "mesh_member_added",
        "routing_algo_set",
        "mesh_interface_up",
        "services_started",
    )

    assert ("routing_algo_set", "mesh_member_added") in violations(late)


def test_a_reversed_sequence_reports_every_rule() -> None:
    """Report all of them, not the first.

    A caller diagnosing a node needs the whole picture; returning on the first
    broken rule would hide the rest behind it.
    """
    assert len(violations(tuple(reversed(GOOD)))) == len(REQUIRED_ORDER)
