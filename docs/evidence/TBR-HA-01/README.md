# Evidence for TBR-HA-01

**Trade:** Safe automatic service recovery

**Trade file:** `docs/trades/TBR-HA-01-safe-automatic-service-recovery.md`

**Priority:** 12 of 16 (SAD v0.31 section 30.2). **Function owner:** SRE + TAK.
**Named owner:** Cameron Zobrist.

**Current contents:** a [manual routed-marker and streaming-worker trial][trial]
records usable iTAK delivery through a forced transit node and a controlled
worker move behind the existing assigned ingress. SQL, broker and durable state
remain on bench. It does not demonstrate automatic recovery or close this trade.

A [later startup observation][startup] records the native SSL container
listening after a bench reboot, a subsequent suspend/resume interruption,
and DNS/sleep repairs. EUD SSL returned; fresh marker UI confirmation was pending.

A [three-node supervision follow-up][supervision] records automatic recovery
after worker/broker faults and one Pi 1 reboot, after private policy installation.
It separates that result from the assisted mixed-carrier chat and from a fresh
main checkout, which does not install the tested policy. The trade stays open.

A [reconciliation record][policy] publishes the private policy that trial rested
on: thirteen systemd drop-ins per node, of which the operative six are
`Restart=always` bounded by `StartLimitBurst=5` over an infinite window, so a
unit is permitted five restarts **ever** and then stops. It also records
`cot-parser` on Pi 1 reaching that limit by itself, giving up, reporting the
failure, and holding that state for eleven hours against `rabbitmq`'s
`Upholds=`, while every sibling unit and the host's default route survived. That
is the shape the closure gate's "stops trying and reports that it has" asks for,
observed rather than injected — so it narrows what an injection must establish
and substitutes for none of it. The same record names where
`services/quadlets/martin.container` has drifted from the deployed articles.

[supervision]: 2026-10-02-supervised-recovery-three-nodes.md
[policy]: 2026-10-02-deployed-recovery-policy-and-repo-divergence.md
[startup]: ../TBR-LINUX-01/2026-10-01-power-ble-followup-node-a.md

[trial]: 2026-10-01-routed-marker-streaming-host.md

This directory exists before the work does, deliberately. The closure gate is
written in the trade file before evidence is gathered, so the result cannot be
graded against a standard invented after seeing it.

## What belongs here

Read the **Closure evidence** and **Closure gate** sections of the trade file
named above. Those sections are transcribed from the SAD and are authoritative;
this file does not restate them, so that the two cannot drift apart.

Every artifact follows the naming and recording rules in
`docs/evidence/README.md`:

- `YYYY-MM-DD-<what>-<node-or-configuration>.<ext>`
- Measurements record instrument, date, node, image build, configuration,
  ambient conditions, and who took them.
- Vendor datasheets go in `datasheets/` with a `.SOURCE.md` recording the
  URL, retrieval date, and document revision. Archive them when you cite them;
  vendors delete PDFs. SAD section 34 is the program's external source register.
- Nothing real: no deployment location, member identity, callsign, credential,
  or operational capture. Strip photograph metadata. See `SECURITY.md`.

**Requires hardware:** Service fault injection runs on an ordinary machine against fakes. The network

## Closing

Evidence here is necessary and not sufficient. SAD section 30.2: a TBR closes
only when its listed evidence exists, **the named owner accepts the evidence**,
and the resulting architecture decision is entered into the persistent ADR
register.

Closing a trade whose named owner is still `TBD-SRR` is not possible, because
there is nobody to accept the evidence. This trade's owner was named on
2026-10-02, so that bar is cleared; it says nothing about whether the evidence
below meets the gate.
