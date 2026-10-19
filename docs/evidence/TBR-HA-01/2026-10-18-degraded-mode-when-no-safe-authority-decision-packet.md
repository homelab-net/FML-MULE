# TBR-HA-01 decision packet: what a MULE does for its EUDs when it cannot reach a safe TAK authority

**State:** `DECIDED` (Owner, 2026-10-18): option A accepted (section 9).

**Trade:** `TBR-HA-01`. **Prepared:** 2026-10-18. **Author:** Claude agent.

**Scope note:**

- This packet decides **degraded-mode service while partitioned**. It does
  **not** decide the trade's recovery mechanism, meaning automatic promotion,
  quorum or fencing. That stays unselected, and this packet closes no closure
  case.
- The Owner's direction is already given: conform to CONOPS 29 as written
  (2026-10-18), with no local TAK server and no change request. This packet turns
  that direction into parameters the bench can build against.

## 1. Why this is on the critical path now

The inserted increment D-1 (`docs/ROADMAP-DEV.md`) needs a MULE's users to keep
communicating when that MULE loses IP reach to the authoritative TAK server.

- **The LoRa gateway is a TAK client,** recorded in
  `docs/evidence/TBR-NET-02/2026-10-18-lora-gateway-as-a-tak-client.md`. With no
  rule for when it transmits, two gateways attached to one server would each
  relay the same traffic.
- **The far side has no server.** Once IP is cut, there is no server for its
  gateway or its EUDs to use.

## 2. Governing constraints

- **CONOPS 29**, lines 1194-1208:
  - "Automatic service recovery shall not create uncontrolled competing
    authoritative stateful services."
  - A partition without safe authority "may remain in: peer ATAK; local S0 and
    S1 services; LoRa/Meshtastic degraded communications".
  - The system "shall prefer loss of shared-service authority over divergent
    authoritative databases".
- **CONOPS 28 and `mule/status.py`:** the vocabulary is `NON-AUTHORITATIVE`, with
  reason `PARTITION`, and it must be visible to the Team Lead.
- **FML-ADR-049:** alive is not ready, and ready is not authoritative.
- **FML-ADR-071:** state boundary. Writes made off the authority are surfaced,
  not merged.
- **FML-ADR-048:** gateway translation is upstream-first. The TAK Meshtastic
  Gateway (option 2) bridges **peer** ATAK multicast to Meshtastic, which is
  exactly the partitioned side's need.
- **CONOPS 2162-2169:** no manual steps for the user.

## 3. Options and cost-benefit

| Option | Pros | Cons |
| --- | --- | --- |
| **A. Peer ATAK plus LoRa bridge** (CONOPS 29 as written) | **No second stateful service**, so no divergent database and nothing to merge on heal; matches the text; option 2 may supply the peer-side bridge | Peer mode carries SA, chat and DMs, not server features (data packages, history, missions); clients must already have multicast enabled; multicast must reach the gateway's host |
| B. A local non-authoritative TAK server | Clients keep a server and its features | An S2 stateful service outside CONOPS 29's list, which needs a change request; reset and inventory on every heal; duplicate-identity risk on heal |
| C. LoRa only, no peer IP | Simplest | Clients on one MULE cannot talk to each other over IP during a partition |

## 4. Recommendation (the Owner decides)

**Option A,** with these parameters:

1. **Mode** is a per-node field, `normal` or `partitioned`, **separate from the
   authority epoch**. A partition never increments the epoch, so a rejoin cannot
   be read as a newer authority.
2. **Detection** is an **application-level** probe of the authority over **mesh
   addresses only**: a TLS session plus an SA round trip. A port check is not
   enough; the 2026-10-17 evidence saw one pass 13 s before the server relayed.
   - The entry threshold, exit threshold and hold time are **`TBD`, set by
     measurement**.
   - Transitions are **rate-limited**, because each one cuts sessions.
3. **The indication.** The node reports `NON-AUTHORITATIVE` / `PARTITION`, and
   its gateway sends a peer chat or status event that **TAK users see**, on entry
   and on exit.
4. **The gateways.**
   - Receive is always on.
   - A partitioned node announces itself on LoRa with a small beacon (mode and
     sequence).
   - **Every gateway relays while any peer's beacon is fresh, or while its own
     node is partitioned.** The authority side's gateway relays for its
     partitioned peers.
   - LoRa→TAK is deduplicated against what the server already carried, by
     message id, which covers partial partitions.
5. **The EUDs.** Each EUD keeps peer ATAK (multicast SA and GeoChat) enabled in
   its package. With the server lost it continues peer-to-peer, and on heal it
   resumes its server stream. **Both behaviours must be shown on real clients
   before anything else is built.**
6. **Identities.** A remote EUD keeps its own uid across bearers (the 2026-10-18
   finding).
   - The gateway's notion of "local client" is reset on every reconnect and mode
     change.
   - Proxies close on mode exit.
   - Claims are accepted only from a roster entry's home node. The roster is a
     bench stand-in for the FML-ADR-087 Mission Trust Service roster.
7. **No local TAK server** is started on any node.

## 5. Consequences

- **What partitioned users lose:** server features (data packages, mission sync,
  server-held history) for the duration. T2 records exactly what.
- **What it costs:** LoRa airtime only while partitioned. T7 sets the PLI rate
  and room policy from measurement.
- **What it changes:** the gateway gains a mode gate and a beacon. The ingress
  gains a mode. Packages gain multicast settings.

## 6. Reversibility and smallest safe prototype

- **Fully reversible:** bench instruments only (`test/bench`). Nothing enters
  `mule/` or `services/`.
- **The smallest prototype** comes before anything else is built: two real
  clients on one network, with the server made unreachable. Does peer SA and chat continue, and
  does the server stream resume on heal? If not, option A fails on these clients
  and this packet returns to the Owner.

## 7. Files that change after approval (not now)

- `test/bench/fml-lora-gw.py`: the mode gate, beacon, dedupe and identity
  resets, with their tests.
- `test/bench/tak-field-ingress.sh`: the mode and the probe.
- The bench fault tool: the partition cut.
- An ADR recording option A, status `CONDITIONAL`, allocated with
  `tools/new-adr.sh`.

## 8. Sources reviewed

- CONOPS v1.2, sections 27-30 and 2162-2175.
- FML-ADR-048, 049, 071, 087.
- `mule/status.py`.
- `docs/evidence/TBR-HA-01/2026-10-17-tak-field-ingress-and-administrative-promotion.md`.
- The `docs/evidence/TBR-NET-02/2026-10-18-*` records.

## 9. Owner disposition

**Accepted, 2026-10-18, Cameron Zobrist (Program Owner):** option A as recommended
in section 4. It records degraded-mode service only: `TBR-HA-01` stays `OPEN`,
its recovery mechanism stays unselected, and nothing closes. The ADR named in
section 7 is allocated with the first bench implementation of these parameters.
