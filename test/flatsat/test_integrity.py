"""Tests that the flat-sat is still a flat-sat.

The value of this directory rests on two properties that no scenario checks,
because a scenario tests the node rather than the arrangement around it:

1. It runs the **real** artifacts. A flat-sat that has quietly forked from the
   node is worse than none, because "it works on the flat-sat" becomes a
   permanent excuse and nobody can tell when it stopped being true.
2. Each fake really implements the interface it claims to. A fake that has
   drifted from its Protocol is a boundary nobody is testing across.

Both were previously enforced by nothing but an import statement and good
intentions.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from mule.power import PowerReadings

from . import node
from .fakes import FakePower, FakeRadio, FakeThermal
from .interfaces import RadioState, ThermalState
from .node import REPO_ROOT

REAL_GENERATOR = REPO_ROOT / "tools" / "gen-config.py"


def test_the_node_calls_the_real_configuration_generator() -> None:
    """Rule 1: the real artifact, not a copy of it.

    `node.py` loads `tools/gen-config.py` by path. If someone replaces that
    with a local reimplementation to make a scenario easier, every region and
    regulatory assertion in this directory silently stops testing the tool a
    node would actually run.
    """
    loaded = Path(node.gen_config.__file__ or "")

    assert loaded == REAL_GENERATOR
    assert loaded.is_file()


def test_the_generator_is_loaded_not_reimplemented() -> None:
    """The node must not carry its own copy of resolution or validation."""
    source = (REPO_ROOT / "test" / "flatsat" / "node.py").read_text(encoding="utf-8")

    assert "gen_config.generate(" in source
    for reimplemented in ("def resolve(", "def validate(", "def load_region("):
        assert reimplemented not in source


@pytest.mark.parametrize(
    ("fake", "protocol"),
    [
        (FakeRadio(), RadioState),
        (FakePower(), PowerReadings),
        (FakeThermal(), ThermalState),
    ],
    ids=["radio", "power", "thermal"],
)
def test_each_fake_satisfies_the_interface_it_stands_in_for(
    fake: object, protocol: type
) -> None:
    assert isinstance(fake, protocol)


def test_the_clock_fake_is_deliberately_not_in_that_list() -> None:
    """`FakeClock` implements `TimeReadings`, which lives in `mule/`.

    Time is the one boundary where the node makes a judgement rather than
    reading a fact, so its Protocol sits beside the code that judges, and that
    code is production per `FML-ADR-051`. This test exists so the omission
    above reads as a decision rather than a gap.
    """
    from datetime import UTC, datetime

    from mule.timekeeping import TimeReadings

    from .fakes import FakeClock

    clock = FakeClock(
        present=True,
        backup_cell=True,
        rtc=None,
        system=datetime.now(tz=UTC),
    )

    assert isinstance(clock, TimeReadings)
    assert not hasattr(clock, "credibility"), (
        "a readings fake must not reach a verdict of its own"
    )
