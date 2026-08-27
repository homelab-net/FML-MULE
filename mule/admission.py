"""Whether a device may join the network.

One question, asked every time a phone or tablet tries to connect: **is the
node in a state where letting this device on is safe?**

It is not a check of *who* the device is. There is no identity, credential or
enrollment anywhere in this repository yet; that waits on `TBR-ID-01` and
`services/mission-trust/`. What this module decides is whether the node itself
is fit to be admitting anyone at all, which is a different and simpler
question, and the one that can be answered honestly today.

The rules are ordered so the most serious refusal is given first, and each
refusal says why in words an operator can act on.
"""

from __future__ import annotations

from dataclasses import dataclass

from .bearers import Bearer, required_not_serving
from .timekeeping import TimeAssessment


@dataclass(frozen=True)
class AdmissionDecision:
    """Whether the device may join, and if not, why not."""

    admitted: bool
    reason: str | None


def decide(
    *,
    booted: bool,
    time: TimeAssessment,
    associated: list[Bearer],
) -> AdmissionDecision:
    """Decide whether a device may be admitted, failing closed on any doubt.

    `FML-ADR-042` is the reason this takes a time assessment rather than
    checking a clock itself: trust validation shall not fail open on invalid,
    implausible or unavailable time, and admission is trust-sensitive. A node
    that cannot trust its clock cannot check a credential's expiry, so it
    refuses rather than proceeding and hoping.

    This is the easiest behaviour in the system to regress, because failing
    open makes the symptom disappear.
    """
    if not booted:
        return AdmissionDecision(False, "node has not booted")

    if time.degraded:
        return AdmissionDecision(False, f"TIME_DEGRADED: {time.reason}")

    not_serving = required_not_serving(associated)
    if not_serving:
        return AdmissionDecision(
            False, f"required bearer(s) not serving: {', '.join(not_serving)}"
        )

    return AdmissionDecision(True, None)
