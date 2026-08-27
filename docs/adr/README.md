# Architecture decision register

Every controlling architecture decision in this program is recorded here as a
numbered document in the `FML-ADR-###` namespace.

The decisions are transcribed from **SAD v0.31 section 0.8**, which is the
controlling register. `docs/architecture/FML-MULE-SAD-v0.31.md` is the source of
rationale; the files here record the decision, its status, its consequences and
its accepted cost with a permanent identifier, and cite the SAD section that
argues it.

Neither replaces the other. A decision described only in the SAD is not citable;
a decision recorded only here has lost its reasoning.

## Identifier rules

Binding. `tools/validate-docs.sh` enforces the mechanical parts.

1. **Identifiers are permanent and never reused.** Not after a decision is
   abandoned, not after a file is deleted, not to close a gap in the sequence. A
   gap in the numbering is information; filling it destroys that information.
   This is governing principle 14 in SAD section 0.3.
2. **Filename is `FML-ADR-###-slug.md`**, three digits, lower-case hyphenated
   slug.
3. **The `id` in frontmatter matches the filename.**
4. **A changed decision does not edit the old one.** Write a new one, set the
   old one's status to `SUPERSEDED` with `superseded-by`, and set `supersedes`
   on the new one. Both directions are recorded.
5. **Every trade an ADR cites must exist** as a file in `docs/trades/`.

Allocate an identifier with `tools/new-adr.sh "Title in sentence case"`. It
reads the highest identifier ever recorded, from the working tree **and from git
history**, so a deleted identifier is never reissued.

## The draft-local AD-001 to AD-020 labels

SAD section 0.8 records that the inline `AD-001` through `AD-020` labels used in
SAD v0.1 and v0.2 were draft-local identifiers, and were **incorrectly reused
when their meanings changed**.

They are historical only and **shall not** be used as controlling decision
identifiers. Nothing in this repository cites them. Where a current decision
carries forward or supersedes one, its own file says so in prose; the
`supersedes` frontmatter field is reserved for `FML-ADR-###` identifiers.

The register starts at 021 for that reason. Identifiers below 021 are consumed
and will not be reissued, except `FML-ADR-000`, which is the template and is
marked `RETIRED` so that it never reads as an active decision.

## Status vocabulary

From SAD section 0.4, extended with the states the register actually uses. The
status is not a confidence rating. It says what kind of commitment the decision
is, which determines what it takes to change it.

| Status | Meaning |
| --- | --- |
| `PROPOSED` | Written, under review, not yet decided. Carries no weight. |
| `SELECTED` | Architecture direction accepted for the current SRR package. Implementation may depend on it. Changing it requires a superseding ADR. |
| `SELECTED PRINCIPLE` | The property is decided; the mechanism that provides it is not. A later ADR names the mechanism **without superseding** this one. |
| `SELECTED TARGET` | An objective the design is being driven toward, not yet demonstrated achievable. |
| `SELECTED PLANNING BASELINE` | Adopted so dependent work can proceed. Expected to be revisited when a named trade closes. Nobody should be surprised if it changes. |
| `PREFERRED` | An implementation candidate currently favoured but replaceable if controlled interfaces remain intact. |
| `CONDITIONAL` | Decided, but contingent on a stated condition. If the condition fails, the decision reverts and the fallback applies. |
| `SUPERSEDED` | Replaced by a later ADR, cited in `superseded-by`. Retained permanently. |
| `RETIRED` | No longer applicable because the thing it decided no longer exists. Not superseded, because nothing replaced it. Retained permanently. |

Three distinctions that matter and are commonly confused:

- **`SELECTED PRINCIPLE` versus `SELECTED`.** `FML-ADR-041` decides that a
  bootable known-good rollback path exists independently of the active root. It
  does not decide whether that is A/B slots, a recovery partition, or something
  else. `TBR-REC-01` selects the mechanism, and the ADR that records it will
  **not** supersede `FML-ADR-041`.
- **`SELECTED PLANNING BASELINE` versus `PREFERRED`.** A planning baseline is
  something dependent work may build on, understanding it may move.
  `FML-ADR-045` is one: power, antenna and BOM planning assume separate radios
  until `TBR-RF-03` proves otherwise. A preference is something nothing may
  build on.
- **`CONDITIONAL`.** `FML-ADR-034` prefers PostgreSQL **only if** the TAK state
  study shows the SQL backend is the correct continuity boundary. The condition
  is stated in the file, and if it fails the decision does not take effect.

## Frontmatter

```yaml
---
id: FML-ADR-021
title: Single primary compute / single Debian host with logical plane isolation
status: SELECTED
date: 2026-08-25
supersedes: none
superseded-by: none
trades: [TBR-COMP-01, TBR-PWR-01, TBR-THERM-01, TBR-HW-01, TBR-CARRIER-01]
verification: Stage 1
---
```

- `status` is one of the values above, spelled exactly.
- `date` is the date the status was last changed. The seed set carries
  `2026-08-25`, the SAD v0.31 issue date.
- `supersedes` and `superseded-by` are an ADR identifier or `none`.
- `trades` is a flow sequence of trade identifiers, or `[]`. Every identifier
  listed must exist in `docs/trades/`.
- `verification` names the CONOPS section 78 qualification stage that validates
  the decision.

## Required sections

Each appears in every ADR. `tools/validate-docs.sh` fails a file missing one.

**Context**, **Decision**, **Status**, **Consequences**, **Accepted cost**,
**Fallback**, **Superseded by**, **Verification dependency**.

**Accepted cost** is distinct from consequences: it is the specific thing
someone will later argue was a mistake. Writing it down before they do is the
point of the section.

## The decision that is deliberately absent

The **TAK automatic-recovery mechanism has no ADR**, by decision. SAD section
0.8 states it remains `TBR-HA-01` and does not receive an identifier until a
mechanism is selected.

Selecting one before `TBR-TAK-01` classifies the mission-critical state would
mean building an HA stack around an unknown continuity boundary. SAD section
14.4 lists the six properties the eventual mechanism must have, without naming
Patroni, etcd, Raft, a witness, a lease, quorum or fencing.

## Status summary

| Status | Count |
| --- | ---: |
| `SELECTED` | 21 |
| `SELECTED PRINCIPLE` | 4 |
| `SELECTED TARGET` | 1 |
| `SELECTED PLANNING BASELINE` | 1 |
| `PREFERRED` | 2 |
| `CONDITIONAL` | 1 |

30 controlling decisions, matching SAD section 0.8.

## Register

`STATUS.md` at the repository root carries the generated current view. This
table is a reading aid and may lag; the generated one does not.

| ID | Decision | Status |
| --- | --- | --- |
| `FML-ADR-021` | Single primary compute / single Debian host with logical plane isolation | `SELECTED` |
| `FML-ADR-022` | Debian stable as production host OS | `SELECTED` |
| `FML-ADR-023` | Consume OpenMANET as reference/configuration source, not mandatory production firmware | `SELECTED` |
| `FML-ADR-024` | IEEE 802.11s + batman-adv/BATMAN-V as baseline IP MANET | `SELECTED` |
| `FML-ADR-025` | High-throughput conventional Wi-Fi as an additional IP bearer | `SELECTED` |
| `FML-ADR-026` | Meshtastic/LoRa remains a separate non-IP degraded plane | `SELECTED` |
| `FML-ADR-027` | RF coexistence controlled through supported host/radio interfaces; no assumed openmanetd primitive | `SELECTED` |
| `FML-ADR-028` | Mission services share the Debian host but cannot directly own network/RF configuration | `SELECTED` |
| `FML-ADR-029` | Rootless Podman + Quadlet is default OCI execution model | `SELECTED` |
| `FML-ADR-030` | Shared-kernel logical isolation using users/namespaces/cgroups/nftables | `SELECTED` |
| `FML-ADR-031` | Stable local DNS + HAProxy/TCP ingress for logical service identities | `SELECTED` |
| `FML-ADR-032` | OpenTAKServer is preferred initial TAK-compatible server | `PREFERRED` |
| `FML-ADR-033` | PyTAK is preferred custom CoT transport/gateway library | `SELECTED` |
| `FML-ADR-034` | PostgreSQL is preferred only if the TAK state study demonstrates it is the correct continuity boundary | `CONDITIONAL` |
| `FML-ADR-035` | MULE service controller is a fixed-policy lifecycle layer, not a cluster scheduler | `SELECTED` |
| `FML-ADR-036` | Smallstep step-ca is preferred initial PKI | `PREFERRED` |
| `FML-ADR-037` | Application-native RBAC first; OPA only when cross-application policy justifies it | `SELECTED` |
| `FML-ADR-038` | EAP-TLS is the production EUD admission target | `SELECTED TARGET` |
| `FML-ADR-039` | WAN overlay terminates on MULE infrastructure, never directly on EUDs | `SELECTED` |
| `FML-ADR-040` | Field kernel/radio-driver promotion is gated and pinned as a tested compatibility set | `SELECTED` |
| `FML-ADR-041` | MULE requires an A/B or equivalently bootable known-good rollback path | `SELECTED PRINCIPLE` |
| `FML-ADR-042` | Battery-backed local RTC + chrony; optional GNSS discipline; credential validity never fails open | `SELECTED` |
| `FML-ADR-043` | Sensitive local mission data uses LUKS2-class block encryption; key-on-same-media unattended unlock is rejected | `SELECTED PRINCIPLE` |
| `FML-ADR-044` | Zeroize is primarily cryptographic key/credential invalidation, not flash overwrite | `SELECTED PRINCIPLE` |
| `FML-ADR-045` | EUD WLAN and high-throughput inter-node mesh are separate logical radio functions; power/BOM planning assumes separate radios until concurrency is proven | `SELECTED PLANNING BASELINE` |
| `FML-ADR-046` | MULE Status Aggregator is approved thin original software | `SELECTED` |
| `FML-ADR-047` | Mission Trust Service is approved thin original software and is not a CA | `SELECTED` |
| `FML-ADR-048` | Gateway translation uses existing OTS/Meshtastic/PyTAK interfaces first; custom translation is protocol-specific glue only | `SELECTED` |
| `FML-ADR-049` | Service Authority Registry is a function of the MULE Status Aggregator, not a separate daemon | `SELECTED` |
| `FML-ADR-050` | Local-storage write amplification is bounded by design through controlled logging/telemetry retention and endurance-qualified storage | `SELECTED PRINCIPLE` |
| `FML-ADR-051` | Node decision logic lives in an importable `mule/` package, not under the test tree | `SELECTED PRINCIPLE` |

## Decisions not yet recorded

The licensing split for this repository (Apache 2.0 for code, CC BY 4.0 for
documentation and hardware artifacts) is a decision that has not been written as
an ADR. It is a repository governance decision rather than a MULE architecture
decision, so it does not belong in the `FML-ADR` namespace as it stands. It is
listed here rather than silently omitted.
