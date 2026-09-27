# CoT `detail` storage preservation and stale handling, observed on the live OTS bench

**Trade:** `TBR-OBS-01`. **Date:** 2026-09-26. **Tier:** `SIMULATED` (observed at
runtime against synthetic data; says nothing about a real client or hardware).
**Taken by:** driving the persistent bench directly. No real identity, location, or
capture; the injected events are obviously synthetic and were deleted afterward
(`SECURITY.md`).

## Why

`FML-ADR-085` (`SELECTED PRINCIPLE`) accepted the upstream-first frame but left the
carrier for FML's added observation semantics (the six state words, provenance,
correlation) to a later implementation ADR, gated on reading whether a CoT consumer
preserves unknown CoT `detail`. The closure gate accepts "the TAK client **or** the
OpenTAKServer code" as the CoT consumer. This reading tests the **OpenTAKServer**
side at runtime; the TAK-client side stays owed.

## Bench

Persistent bench (`/home/mule1/mule/`, `mule-stack.service`): OpenTAKServer
**1.7.13**, image `localhost/fml-bench/ots:1.7.13-py312`, digest
`sha256:762ebf4346de8360d091c0795cc4d22e1f58c16abc4f91df5cf1b407b827cd4e`, PostGIS,
RabbitMQ, nginx-TLS (CoT on 8089 -> 8088). CoT `detail` is a `lax`, skip-validated
open extension point in the archived event schema
(`2026-09-24-event-xsd-version-2.0.xsd`), so an unknown child is schema-legal; this
reading tests whether the consumer keeps it.

## Method

One synthetic CoT event was sent over the TLS 8089 stream with the bench client
certificate (stdlib `ssl`), carrying a standard `<contact>` plus an **unknown**
detail child `<_fml_obs schema="fml.observation/probe" state="active"
source_count="1"/>`, with `stale` set a short interval ahead. The stored row was
read back from Postgres. A second event was injected while a second TLS client was
attached to 8089, to look for the emitted (outbound) copy. All probe rows were
deleted afterward.

## Observations

1. **Storage preserves unknown `detail` verbatim.** The stored `cot.xml` came back
   containing `<_fml_obs schema="fml.observation/probe" source_count="1"
   state="active"/>` with all three custom attributes intact, beside the
   `<contact>`. OpenTAKServer does not strip a detail child it has no column for.
   **This is storage preservation, observed** -- not, on its own, an end-to-end
   round-trip.
2. **The outbound leg was not observed here.** A bare second TLS client attached to
   8089 received no bytes for the injected broadcast event, so this reading does
   **not** demonstrate that the server emits the unknown `detail` to another client.
   OTS routing to a client likely needs more than a raw socket attach (a mission or
   data-feed subscription), which was not set up. Per the closure gate this is a
   limitation, not proof of absence: forwarding is **owed**, not disproven. The
   already-read `route_cot` republishes the parsed event object (source evidence
   that the republish path does not rewrite the event), but that is a source
   inference about the inbound object, not an observed emission of the stored row.
3. **The time trio maps to the record.** `time`/`start`/`stale` parsed into the
   `timestamp`/`start`/`stale` columns, as the schema read in
   `2026-09-27-representation-decision-packet.md` §2a said.
4. **OTS does not implement `FML-REQ-037`; it deletes on a fixed timer.** After
   `stale` passed the row still existed, but only because OTS keeps every row until
   its single global `delete_old_data` (config: 1 week) runs. OTS assigns no
   `expired` state, applies no per-mission-profile retention, and simply omits a
   past-`stale` row from its map response (archived `get_map_state`). So this is
   **not** the `FML-REQ-037` "retained as history for the mission profile's
   retention" behavior; it confirms the opposite -- OTS lacks that semantic, so FML
   must supply it.

## What this answers, and what stays owed

- **Answered (OTS storage):** unknown CoT `detail` survives storage, so the
  `detail` carrier for FML's added semantics is at least storage-viable on the
  server. This is a datum toward `FML-ADR-085`'s owed carrier reading, not its
  completion.
- **Still owed:** (a) the **server's outbound emission** of unknown `detail` to a
  subscribed client, and (b) the **TAK client** (iTAK/ATAK) preserving, forwarding,
  and rendering unknown `detail`, and drawing a past-`stale` event. Both need more
  than this bench read -- a mission/feed subscription for (a), and a client on the
  AP for (b).

Nothing here selects a representation, enters `mule/`, or closes the trade;
`TBR-OBS-01` stays `OPEN`.
