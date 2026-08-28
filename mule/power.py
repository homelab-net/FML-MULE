"""How long the node can keep running, and whether it can say.

CONOPS section 59 sets a planning objective of roughly eight hours on one pack
and is explicit that this is **not a verified minimum**. Section 60 lists what a
mission planning product must address: pack count, mass, charging, external and
vehicle power, cold-weather derating, the service-host power penalty, and
reserve margin. Section 61 makes cold behaviour first-order and forbids treating
the eight-hour figure as winter endurance.

That is a fully specified **procedure** with entirely unmeasured **inputs**.
`TBR-PWR-01` measures the inputs. This module is the procedure, and it is
written now so that closing the trade is a matter of supplying numbers rather
than of writing the code that consumes them.

**With no model, the node says it cannot tell.** That is today's honest answer
and it is what `PowerModel` being optional encodes. It is not a stub: the
decision path around it is complete and tested, and the day `TBR-PWR-01` closes,
one object arrives and the node starts answering.

**Location note.** Production code, per `FML-ADR-051`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

#: Minutes in an hour. Named because a bare 60 in an energy calculation reads as
#: a coincidence rather than a unit conversion.
MINUTES_PER_HOUR = 60


@runtime_checkable
class PowerReadings(Protocol):
    """Raw readings from the power subsystem. Decides nothing."""

    def pack_present(self) -> bool:
        """Whether a protected battery assembly is fitted. CONOPS section 59."""
        ...

    def pack_healthy(self) -> bool:
        """Whether the pack reports itself within its operating envelope."""
        ...

    def state_of_charge(self) -> float | None:
        """Fraction of capacity remaining, or None where nothing reports it.

        None is a real answer, not a gap. Whether the selected assembly carries
        a gauge the node can read is `TBR-PWR-01` and `TBR-HW-01`, and a node
        with a pack it cannot interrogate is a configuration the program has to
        handle rather than assume away.
        """
        ...

    def pack_temperature_c(self) -> float | None:
        """Pack temperature, or None where it is not instrumented."""
        ...


@dataclass(frozen=True)
class PowerModel:
    """The measured numbers a runtime estimate needs.

    Every field belongs to `TBR-PWR-01`. None has a default, for the same reason
    `TimePolicy` has none: there is no defensible value to offer, and a default
    here would become a fielded endurance figure that nobody measured.

    A `PowerModel` in this repository is a **fixture** until that trade closes
    and its evidence is accepted. Nothing may construct one from estimates and
    present the result as an answer.
    """

    #: Usable energy of one fitted pack.
    pack_capacity_wh: float
    #: Fraction held back and never counted as available runtime. CONOPS
    #: section 60 names reserve margin as a planning product input.
    reserve_fraction: float
    #: Node draw with no shared service hosted.
    baseline_load_w: float
    #: Additional draw while hosting shared services. CONOPS section 60 calls
    #: this the service-host power penalty; section 67 asks the operator
    #: whether hosting is reducing runtime, and this is what answers it.
    hosting_load_w: float
    #: Cold derating, as (at or below this temperature, usable fraction),
    #: coldest first. CONOPS section 61 requires derating and forbids treating
    #: the nominal objective as winter endurance.
    cold_derating: tuple[tuple[float, float], ...] = ()

    def usable_fraction_at(self, temperature_c: float | None) -> float:
        """Fraction of capacity usable at this temperature.

        An uninstrumented pack gets no derating, which is optimistic. That is
        deliberate and visible rather than hidden: the alternative is inventing
        a penalty for a temperature nobody measured. `TBR-PWR-01` and
        `TBR-THERM-01` decide whether an uninstrumented pack is acceptable.
        """
        if temperature_c is None:
            return 1.0
        for threshold, fraction in self.cold_derating:
            if temperature_c <= threshold:
                return fraction
        return 1.0


@dataclass(frozen=True)
class PowerAssessment:
    """What the node can say about how long it will keep running."""

    #: None means the node cannot tell, and `reason` says why.
    projected_runtime_minutes: int | None
    #: None where there is no model to compare hosted against unhosted draw.
    hosting_reduces_runtime: bool | None
    #: Why the runtime is unknown. None when it is known.
    reason: str | None
    #: True where a pack is fitted and reports poor health.
    pack_unhealthy: bool


def assess(
    readings: PowerReadings,
    model: PowerModel | None,
    *,
    hosting_shared_services: bool,
) -> PowerAssessment:
    """Estimate remaining runtime, or explain why it cannot be estimated.

    The order matters. Each refusal is distinct, because "no pack fitted",
    "no measured model" and "the pack cannot report its charge" are three
    different situations that an operator would act on differently, and
    collapsing them into one `None` would tell nobody anything.
    """
    unhealthy = readings.pack_present() and not readings.pack_healthy()

    if not readings.pack_present():
        return PowerAssessment(
            projected_runtime_minutes=None,
            hosting_reduces_runtime=None,
            reason=(
                "No battery assembly fitted. The node runs while external power lasts."
            ),
            pack_unhealthy=False,
        )

    if model is None:
        return PowerAssessment(
            projected_runtime_minutes=None,
            hosting_reduces_runtime=None,
            reason=(
                "No measured power model. TBR-PWR-01 has not closed, so the "
                "node cannot estimate runtime and does not guess."
            ),
            pack_unhealthy=unhealthy,
        )

    charge = readings.state_of_charge()
    if charge is None:
        return PowerAssessment(
            projected_runtime_minutes=None,
            hosting_reduces_runtime=model.hosting_load_w > 0,
            reason=(
                "The fitted pack does not report its state of charge, so "
                "remaining energy is unknown even with a measured model."
            ),
            pack_unhealthy=unhealthy,
        )

    load_w = model.baseline_load_w + (
        model.hosting_load_w if hosting_shared_services else 0.0
    )
    if load_w <= 0:
        return PowerAssessment(
            projected_runtime_minutes=None,
            hosting_reduces_runtime=model.hosting_load_w > 0,
            reason="The power model reports no load, which cannot be right.",
            pack_unhealthy=unhealthy,
        )

    usable_wh = (
        model.pack_capacity_wh
        * max(0.0, min(1.0, charge))
        * model.usable_fraction_at(readings.pack_temperature_c())
        * (1.0 - model.reserve_fraction)
    )
    minutes = int(usable_wh / load_w * MINUTES_PER_HOUR)

    return PowerAssessment(
        projected_runtime_minutes=max(0, minutes),
        hosting_reduces_runtime=model.hosting_load_w > 0,
        reason=None,
        pack_unhealthy=unhealthy,
    )
