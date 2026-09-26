# CoT `detail` round-trip and stale retention, observed on the live OTS bench

**Trade:** `TBR-OBS-01`. **Date:** 2026-09-26. **Tier:** `SIMULATED` (observed at
runtime against fakes/synthetic data; says nothing about a real client or
hardware). **Taken by:** driving the persistent bench directly. No real identity,
location, or capture; the one injected event is obviously synthetic and was
deleted afterward (`SECURITY.md`).

## Why

`FML-ADR-085` (`SELECTED PRINCIPLE`) accepted the upstream-first frame but left the
carrier for FML's added observation semantics (the six state words, provenance,
correlation) to a later implementation ADR, gated on reading whether a CoT
consumer preserves and forwards unknown CoT `detail`. The closure gate accepts
"the TAK client **or** the OpenTAKServer code" as the CoT consumer. This reading
answers the **OpenTAKServer** half at runtime; the TAK-client half stays owed.

## Bench

Persistent bench (`/home/mule1/mule/`, `mule-stack.service`): OpenTAKServer
**1.7.13**, image `localhost/fml-bench/ots:1.7.13-py312`, digest
`sha256:762ebf4346de8360d091c0795cc4d22e1f58c16abc4f91df5cf1b407b827cd4e`, PostGIS,
RabbitMQ, nginx-TLS (CoT on 8089 → 8088). CoT `detail` is a `lax`, skip-validated
open extension point in the archived event schema
(`2026-09-24-event-xsd-version-2.0.xsd`: `<xs:any processContents="lax">`,
`<xs:anyAttribute processContents="skip">`), so an unknown child is schema-legal;
this reading tests whether the consumer actually keeps it.

## Method

One synthetic CoT event was sent over the TLS 8089 stream with the bench client
certificate (stdlib `ssl`), carrying a standard `<contact>`/`<remarks>` plus an
**unknown** detail child:

```xml
<detail>
  <contact callsign="FML-OBS-SYNTH"/>
  <remarks>synthetic observation round-trip probe</remarks>
  <_fml_obs schema="fml.observation/probe" state="active" source_count="1"/>
</detail>
```

`time`/`start` were set to now and `stale` to now + 30 s. The stored row was then
read back from Postgres and the probe row deleted.

## Observations

1. **Unknown `detail` is preserved verbatim.** The stored `cot.xml` came back
   containing the `_fml_obs` element with all three custom attributes intact:
   `<_fml_obs schema="fml.observation/probe" source_count="1" state="active"/>`,
   alongside the `<contact>` and `<remarks>`. OpenTAKServer does not strip a detail
   child it has no column for. Combined with the already-read `route_cot`
   (republishes `str(event)` without rewriting it), the server both **stores and
   re-serves** unknown detail. So FML's added semantics (state words, provenance,
   correlation key) **can ride CoT `detail` through the OTS server** rather than a
   custom port or a parallel record.
2. **The time trio maps to the record.** `time`/`start`/`stale` parsed into the
   `timestamp`/`start`/`stale` columns (`2026-09-26 04:25:15` / `…:45`), confirming
   the section 28A age/validity fields land where the earlier schema read
   (`2026-09-27-representation-decision-packet.md` §2a) said.
3. **Past-`stale` is retained, not deleted.** After `stale` passed, the row was
   still present (`now() > stale` true, row count 1). Retention is the separate
   `delete_old_data` deletion (config: 1 week). So on the server, `stale` is a
   presentation filter (`get_map_state` omits a past-`stale` row, per the archived
   source) while the record persists as history until retention deletes it — the
   runtime shape of the `FML-REQ-037` stale-versus-expired-versus-deleted split.

## What this answers, and what stays owed

- **Answered (OTS consumer):** unknown CoT `detail` survives store and re-serve, so
  the `detail` carrier for FML's added semantics is feasible through the server.
  This narrows `FML-ADR-085`'s owed-readings gate: the carrier is no longer
  unbacked; it is server-viable.
- **Still owed (TAK client):** whether a **TAK client** (iTAK/ATAK) preserves and
  forwards an unknown `detail` child on round-trip, and how it presents a
  past-`stale` event, is not shown here. That needs a client on the AP (the
  bookmarked phone-on-AP step). Until it is read, the implementation ADR must not
  assume clients carry the `detail` semantics end to end.

Nothing here selects a representation, enters `mule/`, or closes the trade;
`TBR-OBS-01` stays `OPEN`.
