"""Whether the node is inside its thermal envelope, and whether it can tell.

SAD section 25.7 lists what `TBR-THERM-01` measures: processor, radio, battery,
enclosure and ambient temperature, plus thermal throttling. It determines
whether the selected configuration holds up across the field thermal envelope.

Note which of those is which. **Throttling is a reading**: the compute element
reports that it has throttled, and no judgement is involved. **Being inside the
envelope is a decision**: it compares measured temperatures against limits that
`TBR-THERM-01` has not set. So the comparison lives here and the limits arrive
later, the same arrangement as `power.py` and `timekeeping.py`.

**With no limits the node says it does not know.** That matters more here than
it looks. Before this module existed, the fake reported `within_envelope=True`
by default and the node passed that on, so a node with no defined thermal
envelope was asserting it was inside one. That is a claim about a limit nobody
has measured, which is the thing this repository exists to not do.

**Location note.** Production code, per `FML-ADR-051`.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal, Protocol, runtime_checkable

#: The sensors SAD section 25.7 requires `TBR-THERM-01` to measure. A name here
#: is a place a reading may come from, not a promise that any given build has
#: that sensor fitted; a node reports what it has.
Sensor = Literal["processor", "radio", "battery", "enclosure", "ambient"]

#: What the node can say about its thermal state.
#: `UNKNOWN` is not a failure state. It is the honest answer while no limits
#: exist, or while nothing reports a temperature.
ThermalState = Literal["NOMINAL", "WARM", "CRITICAL", "UNKNOWN"]


@runtime_checkable
class ThermalReadings(Protocol):
    """Raw thermal readings. Decides nothing."""

    def temperatures_c(self) -> Mapping[Sensor, float | None]:
        """Each fitted sensor's reading, or None where it did not report.

        A sensor absent from the mapping is not fitted. A sensor present with
        None is fitted and did not answer, which is a different problem and one
        an operator would act on differently.
        """
        ...

    def throttling_reported(self) -> bool | None:
        """Whether the compute element reports that it is throttling.

        A fact the hardware states, not an inference. SAD section 25.7 lists
        thermal throttling among the things measured rather than derived.

        **None where the platform has no throttle signal**, which is the common
        case: Linux has no portable "am I thermally throttled" flag. It is
        per-SoC, and a board that cannot answer must not be made to say `False`.
        `False` is a claim that the node is not throttling; the absence of a
        signal is not that claim.
        """
        ...


@dataclass(frozen=True)
class ThermalLimits:
    """The temperatures a reading is judged against.

    Every value belongs to `TBR-THERM-01`. None has a default, for the same
    reason `PowerModel` and `TimePolicy` have none: there is no defensible
    number, and a default here would become a fielded thermal limit that nobody
    measured.
    """

    #: Above this, the node is warm but working.
    warn_above_c: float
    #: At or above this, the node is outside its stated envelope.
    critical_above_c: float
    #: Per-sensor overrides as (sensor, warn, critical). A battery and a
    #: processor do not share an envelope, and SAD section 25.7 measures them
    #: separately for that reason.
    per_sensor: tuple[tuple[Sensor, float, float], ...] = ()

    def for_sensor(self, sensor: Sensor) -> tuple[float, float]:
        """Return the (warn, critical) pair that applies to this sensor."""
        for name, warn, critical in self.per_sensor:
            if name == sensor:
                return warn, critical
        return self.warn_above_c, self.critical_above_c


@dataclass(frozen=True)
class ThermalAssessment:
    """What the node concluded about its temperature."""

    state: ThermalState
    #: Reported by the hardware, so it is known even when `state` is UNKNOWN.
    #: None where the platform has no throttle signal at all.
    throttling: bool | None
    #: The hottest reporting sensor, for an operator who wants one number.
    hottest: tuple[Sensor, float] | None
    #: Sensors at or above their critical limit, hottest first.
    breaches: tuple[Sensor, ...]
    #: Why the state is UNKNOWN. None otherwise.
    reason: str | None

    @property
    def outside_envelope(self) -> bool:
        """Whether the node is known to be outside its stated envelope.

        False when the state is UNKNOWN. Not knowing is not the same as being
        fine, and the caller is expected to treat them differently; this
        property answers only the narrow question it names.
        """
        return self.state == "CRITICAL"


def assess(
    readings: ThermalReadings, limits: ThermalLimits | None
) -> ThermalAssessment:
    """Judge the readings against the limits, or explain why it cannot.

    Throttling is passed through in every branch. It is the one thermal fact
    available without a measured envelope, and withholding it because the
    limits are unknown would hide the clearest signal the node has.
    """
    throttling = readings.throttling_reported()
    reported = {
        sensor: value
        for sensor, value in readings.temperatures_c().items()
        if value is not None
    }
    hottest = max(reported.items(), key=lambda item: item[1]) if reported else None

    if limits is None:
        return ThermalAssessment(
            state="UNKNOWN",
            throttling=throttling,
            hottest=hottest,
            breaches=(),
            reason=(
                "No thermal limits. TBR-THERM-01 has not closed, so the node "
                "cannot say whether it is inside an envelope nobody has set."
            ),
        )

    if not reported:
        return ThermalAssessment(
            state="UNKNOWN",
            throttling=throttling,
            hottest=None,
            breaches=(),
            reason="No sensor reported a temperature.",
        )

    breaches: list[tuple[Sensor, float]] = []
    warm = False
    for sensor, value in reported.items():
        warn_at, critical_at = limits.for_sensor(sensor)
        if value >= critical_at:
            breaches.append((sensor, value))
        elif value >= warn_at:
            warm = True

    if breaches:
        breaches.sort(key=lambda item: item[1], reverse=True)
        return ThermalAssessment(
            state="CRITICAL",
            throttling=throttling,
            hottest=hottest,
            breaches=tuple(sensor for sensor, _ in breaches),
            reason=None,
        )

    return ThermalAssessment(
        state="WARM" if warm else "NOMINAL",
        throttling=throttling,
        hottest=hottest,
        breaches=(),
        reason=None,
    )
