# Evidence for the operator status view

**Component:** the MULE Status Aggregator, `FML-ADR-046` (approved thin original
software), with the Service Authority Registry folded in by `FML-ADR-049`.
CONOPS section 67. This directory is component evidence, not a trade's: the
aggregator is an approved decision, not an open `TBR`.

**Why this directory now exists.** The component's hard dependency, `TBR-TAK-01`,
closed 2026-09-06 (`FML-ADR-071`), which defined the mission-state data model and
retired the "inventing a state taxonomy" hazard for the reasoning spine. The
buildable Phase-1 slice -- the operator status roll-up, reusing `mule/status.py`
and served over loopback -- is demonstrated here. Roadmap item 4.7.

**What belongs here.** `SIMULATED` bench demonstrations of the operator view, and
later the fielded component's artifacts once `TBR-HA-01` (the Service Authority
Registry) and `TBR-COMP-01` (the resource envelope) close. Naming and recording
rules are in `docs/evidence/README.md`. Nothing real: no deployment location,
member identity, callsign, credential, or operational capture. See `SECURITY.md`.

**Out of scope here** (still gated): the Service Authority Registry and the
`shared_data_authoritative`/`data_stale` fields (`TBR-HA-01`), a fielded daemon
(`TBR-COMP-01`), a production mesh-links reader (parked on
`TBR-RF-01`/`TBR-RF-03`/`TBR-LINUX-01`), and the I2C display (hardware).
