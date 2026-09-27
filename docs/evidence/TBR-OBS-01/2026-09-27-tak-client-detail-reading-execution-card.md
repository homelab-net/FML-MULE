# TBR-OBS-01 execution card: read a TAK client's handling of unknown CoT `detail` and a past-`stale` event

**Trade:** `TBR-OBS-01`. **Prepared:** 2026-09-26. **Status:** procedure to run, not
a result. Nothing here is `SIMULATED` or `HARDWARE-VERIFIED` until executed and the
results recorded. No real identity, location, or capture; synthetic events only
(`SECURITY.md`).

## Finding and authority

- **Finding:** `TBR-OBS-01`, the **TAK-client** half of the consumer reading that
  `FML-ADR-085` gates the observation implementation ADR on.
- **Governing records:** `FML-ADR-085` (owed readings), the `TBR-OBS-01` closure
  gate ("for a CoT behavior that is the TAK client or the OpenTAKServer code"), and
  the server storage reading `2026-09-26-cot-detail-storage-on-ots.md`.
- **Why:** the storage reading showed OpenTAKServer preserves an unknown CoT
  `detail` child in storage, but left two things owed: whether the server **emits**
  it to a subscribed client, and whether a **TAK client** (iTAK/ATAK) preserves,
  forwards, and renders it -- and how the client draws an event after `stale`
  (`FML-REQ-035`). The client is the decisive consumer for the carrier question: if
  the client discards unknown `detail`, FML's added semantics cannot ride it
  end to end (the `FML-ADR-070` failure shape).
- **Boundary:** executing this produces a behavioral reading of the upstream
  consumer, the gate's requirement. It does not select a representation, enter
  `mule/`, or close the trade.

## Prerequisites

The live bench up (`/home/mule1/mule/`, `mule-stack.service`), and a phone with
iTAK on the MULE AP, enrolled to the bench OTS with `datapkg/MULE-FML-iTAK.zip`
(the phone-on-AP step bookmarked for the offline-map test; the Pi arriving the
weekend of 2026-09-27 is the arm64 AP article for this).

## Steps

### Step 1 -- iTAK receives an event carrying unknown `detail`

Inject a synthetic CoT event (fake uid, near-future `stale`) with an unknown detail
child `<_fml_obs schema="fml.observation/probe" state="active" source_count="1"/>`
into OTS (the storage-reading injector script over TLS 8089). Record: does the event
appear on the iTAK map, and does the client accept it without error.

### Step 2 -- does the client preserve/forward the unknown `detail`

Have iTAK act on the event (e.g. edit/redistribute, or observe its periodic
re-broadcast) and capture the CoT the client emits (a second subscribed client, or
the OTS-stored copy of the client's outbound event). Record whether `_fml_obs`
survives in what the client sends. This is the end-to-end carrier question.

### Step 3 -- how the client draws a past-`stale` event (`FML-REQ-035`)

Inject an event with `stale` a few seconds ahead; watch the iTAK marker across the
`stale` boundary. Record the client's behavior: does it grey, dim, remove, or keep
the marker, and after how long. This is the client-side performance of "a stale
observation is not presented as current."

### Step 4 -- server outbound leg (closes the storage-reading limitation)

With a real client subscribed, confirm whether OTS emits the injected unknown
`detail` to it (the headless bare-socket attempt saw nothing; a real iTAK
subscription is the correct client). Record what the client receives.

## What each step informs

| Step | Reading it supplies |
| --- | --- |
| 1 | client accepts an unknown-`detail` event (`FML-REQ-034` carrier, ingress) |
| 2 | client preserves/forwards unknown `detail` end to end -- the decisive carrier datum |
| 3 | client presentation of a past-`stale` event (`FML-REQ-035`) |
| 4 | server outbound emission of unknown `detail` (the storage reading's owed leg) |

## Boundary this card must NOT cross

No real identities/captures; synthetic events only, deleted after. Recording these
readings lets the **implementation ADR** decide the `detail` carrier and assign the
section 28A behaviors to local policy; it does not, by itself, close `TBR-OBS-01`,
which the named Owner closes by accepting how an observation is recorded and
presented.
