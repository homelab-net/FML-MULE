# TBR-OBS-01 decision packet: how a mission observation is recorded and presented

**Trade:** `TBR-OBS-01`. **Prepared:** 2026-09-26. **Author:** Claude agent.
**Disposition:** `ACCEPTED (frame)` -- Owner, 2026-09-26, recorded in
`FML-ADR-085`. The Owner accepted this packet's **frame** (upstream-first; CoT as
carrier where a CoT path already carries the meaning) after an independent
red-team, **not section 4 as written**: the metadata carrier, the state-model
thresholds, the retention-as-history bound, and the assignment of
`FML-REQ-034`/`035`/`037`/`038`/`040` to local policy are deferred to a later
**implementation ADR** gated on the owed CoT-`detail` and TAK-client readings (see
section 4a). `TBR-OBS-01` **stays `OPEN`**; this packet selects no representation,
freezes no field names, and writes nothing into `mule/`, `regions/`, or a schema.
Analysis tier: not `SIMULATED` (except the section 2a bench read), not
`HARDWARE-VERIFIED`.

## 1. What this decides, and why it is the critical path

CONOPS v1.2 section 28A (`FML-REQ-034`-`041`, all STAGE-01) commits the program to
a mission observation that carries its age, source, and state, that is not
presented as current once stale or expired, whose observed time survives relaying,
that is retained as history after expiry, that is not merged across subjects, whose
link reports are not read as paths or emitter locations, and whose derived products
cite their sources. `TBR-OBS-01` owns **how** that is recorded and presented, and it
is `OPEN`: no representation is selected, and the trade file bars any of this
behavior from entering `mule/` until an ADR records the choice. The entire
awareness enhancement (sensing, tasking, comms-terrain, SITREP, EMCON collection)
produces or consumes observations, so this one decision gates all of it.

## 2. What is already established (cited, not re-derived)

The 2026-09-24 comparison (`2026-09-24-representation-comparison.md`) and consumer
reading (`2026-09-24-consumer-reading.md`) already read a CoT `Event`, the
OpenTAKServer 1.7.13 `cot` path, and Meshtastic firmware `v2.8.0.47db0e3`. The
closure gate accepts "the TAK client **or the OpenTAKServer code**" as the CoT
consumer, so the archived OpenTAKServer excerpts are a valid reading for the CoT
behaviors OTS performs. From them:

- **CoT carries the timing.** A CoT event has `time`, `start`, and `stale`
  (`2026-09-24-event-xsd-version-2.0.xsd`); `stale` is the instant after which the
  event should no longer be considered valid.
- **A server performs a stale-hide, on one timestamp.** OTS `get_map_state` returns
  markers/range-bearing/casevac only when `CoT.stale` is at or after the server
  clock (`2026-09-24-opentakserver-1.7.13-map-state.py.txt`), i.e. it omits a
  past-`stale` row. But it is **one timestamp**: it cannot say *stale* versus
  *expired*, and an omitted row is not presented as history.
- **A server performs retention-by-deletion.** OTS `delete_old_data` removes old
  rows on a schedule (`2026-09-24-opentakserver-1.7.13-scheduled-jobs.py.txt`,
  default one week, `...-delete-old-data-default.txt`). Deletion is not
  "retained as history."
- **The relay path does not restamp; a converter does.** OTS `route_cot`
  republishes the event without replacing `time`
  (`...-route-cot.py.txt`), but the Meshtastic-to-CoT builder stamps the server
  clock onto `time`/`start`/`stale` (`...-meshtastic-cot.py.txt`) — the exact
  substitution `FML-REQ-036` forbids when that event is then treated as the
  observation.
- **No read consumer assigns the six state words**, records a possible match as
  distinct from a confirmed identity, names a derived product's source
  observations, or records a bounded-queue discard without ending participation
  (`2026-09-24-consumer-reading.md`, "What these consumers do not define").

## 2a. Observed on the live OTS bench (2026-09-26, `SIMULATED`)

The source reading above was confirmed at runtime against the persistent bench
(`/home/mule1/mule/`, `mule-stack.service`): OpenTAKServer **1.7.13** (image
`localhost/fml-bench/ots:1.7.13-py312`,
`sha256:762ebf4346de8360d091c0795cc4d22e1f58c16abc4f91df5cf1b407b827cd4e`, whose
version string is 1.7.13, believed to correspond to the git tag the archived source
is pinned to -- an image and a tag/commit are different artifacts, so the
correspondence is asserted from the version string, not verified byte-for-byte),
PostGIS, RabbitMQ, nginx-TLS. Only
the running database **schema** and the OTS **scheduled-job config** were read; no
stored mission rows were read or copied (row contents are out of scope and would be
a capture; `SECURITY.md`). This is observed runtime state, `SIMULATED` tier; it
selects no representation and closes nothing.

- **Record shape.** The `cot` table's columns are exactly: `id, how, type,
  sender_callsign, sender_device_name, sender_uid, recipients, timestamp, start,
  stale, xml, mission_name, uid`. A stored observation therefore carries the CoT
  time trio (`timestamp`/`start`/`stale`) and a producer (`sender_uid` /
  `sender_callsign`) — the age and source of `FML-REQ-034` — plus the raw `xml`.
  There is **no column holding any of the six state words**; the running store
  confirms the source finding that `new/active/stale/expired/merged/superseded` is
  not a field OTS keeps.
- **Retention is deletion.** The running config sets `OTS_DELETE_OLD_DATA_WEEKS: 1`
  (all finer units `0`) and registers `delete_old_data` as a scheduled job. Live
  retention is enforced by **deletion**, confirming at runtime that OTS does not
  "retain as history" — the divergence `FML-REQ-037` requires FML to add.

This runtime read confirms the **record shape and retention** only. It does **not**
show the dynamic stale-hiding presentation (the `get_map_state` omission) or the
client-side (iTAK) rendering of a past-`stale` marker; observing those needs an
authenticated API / CoT injection and a client on the AP, and is deferred (the
client-side reading remains the limitation in §3).

## 3. The consumer reading this packet could not obtain (limitation, per the gate)

The gate: "If that consumer cannot be read, the ADR records the limitation. It does
not treat the unread consumer as proof that the behavior is absent." How a **TAK
client** (ATAK/iTAK/WinTAK) draws an event after `stale` — the canonical client-side
performance of `FML-REQ-035` — was not read here. A byte-faithful excerpt of client
source could not be archived from this environment (no repository/network archive
access, and the available fetch path returns processed text, not the verbatim,
line-ranged, hashable source the evidence convention requires). This is recorded as
a limitation, not as absence. **Before the ADR assigns client-side stale
presentation to local FML policy, a TAK-client reading is required** (or the ADR
records that OTS server-side omission is the accepted consumer for that behavior).

## 4. Recommendation (the Owner decides each)

Adopt **CoT as the observation carrier where CoT already carries the meaning, and
add a small, explicitly-named FML metadata layer for the section 28A behaviors no
read consumer performs** — rather than a new program-wide JSON wire format
(consistent with `FML-ADR-048` upstream-first and the handoff's "semantic contract,
not a universal wire protocol"). Concretely, per requirement:

| Req | Carried by CoT / a read consumer | FML must add (and its status) |
| --- | --- | --- |
| 034 age/source/state (6 words) | `time`/`start` (age), event `uid` and a producer field (source) | The six explicit words `new/active/stale/expired/merged/superseded` as node-local state — **no consumer performs this**; new FML policy |
| 035 stale not current | OTS server omits past-`stale` (cited) | Client-side presentation — **limitation (§3)**; and the stale-vs-current split as local state |
| 036 relay keeps observed time | `route_cot` does not restamp (cited) | Keep `observed_at` distinct from `received_at`; never treat a converter's server-clock event as the observation |
| 037 expired kept as history | OTS `delete_old_data` **deletes** (cited) — the opposite | Retain-as-history for a mission-profile duration — **no consumer performs this**; new FML policy |
| 038 no false merge | none (no consumer correlates) | Deterministic, capability-keyed correlation only; a possible match is never a confirmed identity — new FML policy |
| 039 link report is not a path/location | Meshtastic neighbor packet carries node id + SNR, no coordinate, no path claim (cited) | Enforce the guard when a link observation is represented |
| 040 derived product cites sources | none | Provenance list + source count on a derived product; a model product labelled as one — new FML policy |
| 041 full queue records discard | Meshtastic drops oldest + logs (cited), but the log is not a discard record and says nothing of participation | A discard record that does not, by itself, end local participation — new FML policy |

The state model recommended for the Owner's acceptance: **active** while
`now < stale`; **stale** while `now ≥ stale` and within the mission-profile
retention; **expired** past retention, **retained as history, not deleted** (the
deliberate divergence from OTS `delete_old_data` that `FML-REQ-037` requires);
`new`, `merged`, `superseded` as correlation-layer states. Every value that varies
by capability (the `stale`/TTL source, the retention duration) is mission/profile
data with no compiled-in default, following the `TimePolicy`/`CapabilityPolicy`
discipline — not fixed in this packet.

## 4a. Acceptance, and what was NOT accepted (2026-09-26, after red-team)

An independent read-only red-team judged section 4 sound as a **frame** but reading
as *decided* on points the closure gate and CONOPS do not yet license. The Owner
accepted accordingly. `FML-ADR-085` records the accepted frame; it is authoritative
where it and section 4 differ.

**Accepted (the frame):** observations are upstream-first; CoT is the carrier for
every meaning an upstream CoT path already carries; the observed time is preserved
through relay (`FML-REQ-036`, the one behavior a read consumer performs); and the
deliberate divergence from OTS `delete_old_data` (deletion) toward retain-as-history
for `FML-REQ-037` is correctly identified.

**Not accepted as decided -- deferred to the implementation ADR, gated on the owed
readings:**

- **The carrier for the FML-added semantics** (the six state words, provenance,
  correlation) is a **candidate, not a selection.** Whether they ride CoT `detail`
  turns on whether the TAK clients this program uses preserve and forward unknown
  `detail` on round-trip -- the closure gate bars assigning a semantic to `detail`
  until that schema and a client path are read, and neither is. State kept
  node-local only would be invisible across the COP, so "node-local metadata" is not
  a sufficient answer on its own.
- **The state model** (the stale/expired thresholds and the retention-as-history
  duration) is a **candidate.** The implementation ADR derives the thresholds from
  `FML-REQ-037` and bounds the history, reconciled with `FML-ADR-050` (retention is
  the bound; "not deleted" must not mean "kept forever"). `new`/`merged`/
  `superseded` have no design yet.
- **`FML-REQ-034`/`035`/`037`/`038`/`040`** are **not assigned to local FML policy
  here**; only `FML-REQ-036` has a read consumer today. The rest wait on the owed
  readings per the closure gate.
- **Mesh-only observations** (a link-heard report, `FML-REQ-039`) have **no upstream
  CoT path** -- the read consumer does not convert them -- so CoT-carrier is right
  *where a CoT path exists*, and this sub-case is handled by conversion glue
  (`FML-ADR-048`) in the implementation ADR, not by assuming CoT.

## 5. Consequences and what this must NOT do

- Accepting this **frames** the representation; it does not by itself satisfy any
  `FML-REQ`. Each behavior tagged "new FML policy" still needs its consumer reading
  (or a recorded limitation) in the ADR, per the gate.
- It does **not** select a wire format, freeze field names, create an
  awareness/fusion daemon, or turn the Status Aggregator into an observation store
  (`FML-ADR-051`/`052`; the handoff §1.3). `mule/status.py`'s `Observations` is not
  a section 28A observation and is not extended here.
- The implementation layer (a pure `mule/` decision function exercised by the
  digital twin, versus a `test/`-only demonstration first) is left to the ADR and
  the `mule/` entry discipline; this packet writes no code.

## 6. Reversibility and smallest safe next step

Fully reversible: this is a document. Smallest next step after acceptance: create
the representation ADR (`tools/new-adr.sh`), citing the comparison and the consumer
readings above and recording the client-reading limitation; then a `test/`
fixture + digital-twin scenario demonstrating the accepted lifecycle/correlation
semantics before any promotion to `mule/`.

## 7. Sources reviewed

`docs/evidence/TBR-OBS-01/2026-09-24-representation-comparison.md`,
`2026-09-24-consumer-reading.md` and the OpenTAKServer 1.7.13, Meshtastic
`v2.8.0.47db0e3`, and CoT `Event` v2.0 excerpts archived beside them (provenance in
`2026-09-24-consumer-reading.SOURCE.md` and `2026-09-24-upstream-snapshots.SOURCE.md`);
CONOPS v1.2 section 28A; `docs/verification/requirements.md` (`FML-REQ-034`-`041`);
the `TBR-OBS-01` trade file (closure gate); `FML-ADR-048`, `FML-ADR-050`,
`FML-ADR-051`, `FML-ADR-052`; and the live OTS bench observation in section 2a
(OpenTAKServer 1.7.13, `mule-stack.service`, 2026-09-26 — schema and retention
config only).

## 8. Owner disposition

`ACCEPTED (frame)` -- Owner, 2026-09-26, recorded in `FML-ADR-085`
(`SELECTED PRINCIPLE`). An independent red-team found section 4 sound as a
**frame** but over-stated as a selection on three points, so the acceptance is of
the frame with those points deferred to the implementation ADR (section 4a).
`TBR-OBS-01` stays `OPEN`: the frame is decided, closure still needs the owed
readings and the carrier decision.
