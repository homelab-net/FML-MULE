# GAP-09F decision packet: the one real milestone service

**State:** `IMPLEMENTED`. The Program Owner selected **Martin serving one
read-only per-mission MBTiles file** in the Codex thread on 2026-09-24. The
GAP-09 umbrella gate still requires independent review before closure.

**Finding:** GAP-09F. **Prepared:** 2026-09-21. **Author:** Claude agent,
redirected from Codex by the Owner. **Independent verifier:** a separate agent,
assigned at execution time (this author will not verify its own work).

## 1. Decision requested

Which single real service is the v0.0.1 milestone service that a phone reaches
over the AP, and in what content format? Everything downstream -- the 09G
deployment unit, 09H operator steps, and 09I acceptance -- depends on this answer.

## 2. Governing constraints

- The v0.0.1 slice is narrow: **no** HaLow, mesh, LoRa, TAK beyond this service,
  identity, or rollback (REMEDIATION line 630).
- `FML-ADR-078`: only a catalog entry with an **existing loadable unit and a
  pinned image** may be enabled. `services/catalog/catalog.yml` has both
  candidates at `image: TBD` / `unit: TBD` today.
- CLAUDE.md: OCI images by **immutable digest, never a tag**.
- `FML-ADR-029`: rootless Podman + Quadlet.
- Closure gate (REMEDIATION line 681): a phone associates and reaches the named
  real service; **no placeholder** satisfies it.

## 3. Candidates (from the OSS-01 prior-art register)

| Candidate | Serves | License | Pinnable image? | Resource (x86, SIMULATED) | Durable state / `TBR-HA-01` exposure | Content format |
| --- | --- | --- | --- | --- | --- | --- |
| **Martin** | map tiles `z/x/y` | MIT OR Apache-2.0 | **Yes** -- a digest was pinned and benched 2026-09-06 | ~8.5 MB idle / 27-30 MB peak RSS; ~650 MB image | **None** (read-only mount) -> minimal | one read-only MBTiles per mission (`FML-ADR-073`) |
| Kiwix | offline reference content | GPL-3.0-or-later (+ libkiwix/libzim) | likely (confirm a pinned digest) | not benched here | none (read-only ZIM) -> minimal | ZIM |
| OpenTAKServer | TAK | GPL-3.0-or-later | **No** -- no complete official image; a 3-process build must be defined | ~536 MB (3 procs) + PostgreSQL + RabbitMQ | **durable TAK state** -> significant | CoT/TAK |
| NOMAD content, Kolibri, ProtoMaps/PMTiles | content / map provisioning | mixed | n/a | n/a | n/a | provisioning/format references, **not** clean single-service runtime selections |

## 4. Recommendation accepted by the Owner

**Martin, serving one read-only per-mission MBTiles file (`FML-ADR-073`), as the
v0.0.1 milestone service.** Reasons:

- It is the **only candidate with a pinned, already-benched OCI image**, so it
  needs no out-of-scope image build (OTS would; Kiwix's pinned digest is
  unconfirmed).
- It is **tiny, rootless, and read-only**, so it barely touches the **open
  `TBR-HA-01`** recovery question -- recovery is re-pull/restart, not a durable-state
  design.
- **MIT/Apache** license (clean), versus GPL-3 for Kiwix/OTS.
- It is **already the approved map service** (`TBR-MAP-01`, `FML-ADR-073`), so the
  milestone **reuses an approved component** rather than introducing a new
  architecture -- the smallest honest "a phone reaches a real service" slice.

Alternatives, stated fairly:

- **Kiwix** -- choose this if the milestone should be *reference content* rather
  than maps. Viable and read-only, but GPL-3, not benched here, and its pinnable
  digest must be confirmed.
- **OpenTAKServer** -- the eventual real TAK server, but **not** a v0.0.1 milestone:
  it forces an out-of-scope image build (reopening the OTS-build/arm64 work),
  carries durable state + real HA exposure + insecure upstream defaults. Defer to a
  later phase.

## 5. Consequences

- **Image:** Martin -- a fresh digest-pinned build/profile is still required per
  the Martin intake, but no from-scratch build. OTS -- a build sub-task. Kiwix --
  confirm a pinned digest.
- **HA/recovery (`TBR-HA-01`, OPEN):** this packet sets **no** restart policy; the
  chosen service's exposure to that open trade is a selection consequence, not a
  decision made here.
- **arm64:** deferred (x86 dev article first); confirm multi-arch at pin time
  (`GAP-09F/G` / GAP-09 image work), out of this packet's scope.
- **Resource:** Martin ~tens of MB; OTS ~536 MB + DB + broker (pushes the
  `TBR-COMP-01` memory class).

## 6. Reversibility and smallest safe prototype

The choice sets the 09G deployment unit; changing it later means redoing 09G, not
a data migration. The smallest prototype already exists: the 2026-09-06 Martin
read-only-tile bench; the milestone extends it to the phone-over-AP path.

## 7. Files and acceptance criteria after approval

GAP-09G enables Martin, pins its image and unit in
`services/catalog/catalog.yml`, adds a rootless Quadlet under
`services/quadlets/`, and records the implementation under
`docs/evidence/findings/GAP-09G/`. GAP-09I remains the separate acceptance: a
phone reaches this selected profile over the AP.

## 8. Sources reviewed

`docs/prior-art/martin.md`, `opentakserver.md`, `offline-content-and-maps.md`,
`registry.yml`; `docs/evidence/TBR-MAP-01/`,
`docs/evidence/TBR-COMP-01/2026-09-06-service-plane-steady-state-footprint.md`;
`FML-ADR-073`, `FML-ADR-078`, `FML-ADR-029`; REMEDIATION Phase 3, lines 654-656.

## 9. Owner disposition

**Approved 2026-09-24:** Martin, serving one read-only per-mission MBTiles file.
The Owner's direction was: "Use Martin and let's press." The implementation
pins the official Martin 1.16.1 multi-architecture image index at
`sha256:59902019bf9038926ff0c71174237d6852e64c457830a6349abe7090be8818ca`.
