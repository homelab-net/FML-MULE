# GAP-09D evidence

This directory records the MULE runtime-packaging decision (entry point,
installation/versioning model, systemd unit shape) for the v0.0.1 vertical slice.

State: OPEN -- decision packet prepared, `AWAITING_USER_DECISION`. The runtime
entry point and installation model are an architectural decision requiring a new
implementation ADR; no code is written until approved.

| Artifact | What it records |
| --- | --- |
| `decision-packet.md` | Entry-point-form options, the installation/versioning model against `FML-ADR-040`, the unit shape with restart/naming deferred to `TBR-HA-01`/`TBR-LINUX-01`, recommendation, and requested Owner disposition. |
