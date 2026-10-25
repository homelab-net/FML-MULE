# TBR-HA-01 decision packet: a per-MULE relay for partitioned iTAK users

**State:** `AWAITING_USER_DECISION`. Commissioned by the Owner on 2026-10-24
(section 9 of the [degraded-mode packet][degraded]).

**Trade:** `TBR-HA-01`. **Prepared:** 2026-10-25. **Author:** Claude agent.

**Scope note:**

- This packet decides whether a MULE serves **its own iTAK users while it is
  partitioned**, and how. It changes nothing for clients with a peer path,
  which option A already serves.
- Accepting a relay **amends parameter 7** of the degraded-mode packet ("no
  local TAK server is started on any node"). That is why the Owner asked for it
  to be decided on its own.
- It does not decide the trade's recovery mechanism (promotion, quorum or
  fencing), and it closes nothing.

## 1. Why this is on the table

The degraded-mode packet's [prototype][prototype] found that **iTAK has no peer
path**: with iTAK running for 83 s, a counter on the access point saw it send no
multicast or broadcast at all, while WinTAK sent on both of its interfaces. When
its MULE loses the authority, an iTAK user can talk to nobody, including the
WinTAK user beside them, until the partition heals. The Owner scoped option A to
peer-capable clients and asked what serving iTAK would take.

One thing iTAK does do is reconnect on its own: it came back to the server 38 to
49 s after each lift. So a MULE can serve it only by giving it **a server to
reconnect to**, which is what a relay is.

## 2. Governing constraints

- **CONOPS 29:** a partition "may remain in: peer ATAK; local S0 and S1
  services; LoRa/Meshtastic degraded communications". Recovery "shall not
  create uncontrolled competing authoritative stateful services", and the system
  "shall prefer loss of shared-service authority over divergent authoritative
  databases".
- **CONOPS section 9 classes:** S1 functions "should remain locally available
  where practical even when all external service hosts are absent", and its
  first example is "peer-to-peer ATAK". S2 functions "use shared state or
  central coordination", and its first example is "TAK Server".
- **The Owner's direction of 2026-10-18:** conform to CONOPS 29 as written, with
  no local TAK server and no change request.
- **FML-ADR-071:** writes made off the authority are surfaced, not merged.
- **CONOPS 2162-2169:** no manual steps for the user.
- **The degraded-mode packet's parameters 1 to 6** stand: mode separate from the
  epoch, detection by probe, the visible indication, the gateways' relay rule,
  identity resets, and proxies closed on mode exit.

## 3. Options and cost-benefit

| Option | Pros | Cons |
| --- | --- | --- |
| **A. No partition service for iTAK** (today's scope) | Nothing to build; parameter 7 stands | An iTAK user is cut off from everyone, the next user included, for the whole partition |
| **B. A stateless relay on each MULE**, live only while partitioned | iTAK users reach local users of any client, and LoRa, with no manual step. It holds nothing, so on heal there is nothing to merge and nothing to diverge | Amends parameter 7. iTAK must find it at the address it already uses, so the relay presents the service's certificate, which then sits on every MULE. Two session changes per partition. Server features stay lost |
| C. A local non-authoritative TAK server (the degraded-mode packet's option B) | Clients keep server features | A stateful S2 service off the authority, which needs a change request; reset and inventory on every heal; duplicate identities on heal. Not chosen on 2026-10-18 |

**What B holds.** No database, no history, no data packages, no disk. It
fans each event a client sends out to the other local clients, to the MULE's
peer multicast, and to the gateway, and forgets it. That is the case for
calling it S1: it carries for iTAK what "peer-to-peer ATAK" carries for
clients that can multicast, with no shared state and no coordination. The case
against is that iTAK sees a TAK server, which is S2's first example. It is a
judgement the Owner makes, not one this packet can settle. If the Owner rules
it S2, B needs a change request like C.

## 4. Recommendation (the Owner decides)

**Option B, gated,** with these parameters. None is built until the gates in
section 6 pass.

1. **Live only while partitioned.** The relay runs, and the MULE's ingress
   sends `tak.field`'s stream to it, only while the node's mode is
   `partitioned`. Entry and exit are the degraded-mode packet's detection, so
   the [detection sweep][sweep]'s values apply once the Owner accepts them.
2. **Stateless.** It keeps events in memory only to fan them out, and nothing
   survives a mode exit or a restart. It serves no data packages, missions or
   history; a client asking for one is refused, not queued.
3. **Who it accepts.** Mutual TLS against the field CA, and only clients on
   the MULE's own roster: the bench stand-in for the FML-ADR-087 Mission Trust
   Service roster, as parameter 6 already uses for claims.
4. **What it bridges.** Local stream clients to each other; to the MULE's
   peer multicast, so a WinTAK user beside an iTAK user sees them; and to the
   LoRa gateway, which connects to it as it connects to the server today. Every
   bridged event is deduplicated by message id, as parameter 4 already requires
   of the gateways.
5. **The indication** is the degraded-mode packet's parameter 3, sent on the
   relay too, so an iTAK user is told they are partitioned.
6. **Heal.** On mode exit the relay closes every session (parameter 6), the
   ingress returns to the authority, and clients reconnect. What the relay
   carried is not on the authority. It is listed, not merged (FML-ADR-071, and
   D-1's heal step "what peer mode could not carry is listed").

**What B does not solve.** The prototype's first finding still stands: nothing
sent toward the authority during a partition arrives later. The relay gives an
iTAK user someone to talk to; it does not hold and resend what they send to
users on the far side. That remains its own question.

## 5. Consequences

- **What partitioned iTAK users gain:** SA and chat with everyone on their own
  MULE, of any client, and with the far side over LoRa.
- **What they still lose:** server features, and anything sent across the
  partition that LoRa cannot carry.
- **What it costs:**
  - **Two session changes per partition,** each one an outage for iTAK: at heal
    the prototype measured 38 to 49 s. Entry is unmeasured.
  - **The service certificate's key on every MULE.** Anyone who takes a MULE
    can then stand up a convincing `tak.field`. Whether a relay-only
    certificate can be one iTAK accepts is the first thing to find out.
  - **A new component:** the relay, its mode gate, and an ingress mode.

## 6. Reversibility and smallest safe prototype

- **Fully reversible:** bench instruments only (`test/bench`), as with option
  A. Nothing enters `mule/` or `services/`.
- **Gate 0, before anything is built:** confirm on the iTAK build in use that it
  has no peer or mesh setting. The prototype did not exclude one. If one
  exists, option A serves iTAK and this packet is withdrawn.
- **Gate 1, the smallest prototype:** one iTAK client, one MULE, the ingress
  switched by hand (no detection yet), and the relay as a bench script. Does
  iTAK reach the relay with no manual step, and how long does it take? Does it
  accept the relay's certificate, and which certificate? Does chat cross between
  iTAK and WinTAK through the relay? Does iTAK return to the authority on heal?
  If iTAK will not move without a manual step, B fails and the scope stands.
- **Candidates for the relay:** a small CoT fan-out is a few hundred lines. An
  existing lightweight server is checked first against parameter 2; whether
  one can run with no persistent state is unverified.

## 7. Files that change after approval (not now)

- A new bench relay in `test/bench`, with its tests.
- `test/bench/tak-field-ingress.sh`: the partitioned route to the relay.
- `test/bench/fml-lora-gw.py`: connecting to the relay while partitioned.
- The degraded-mode packet's parameter 7, amended to name the relay.
- If the Owner rules the relay S2: a change request under `docs/change-requests/`.

## 8. Sources reviewed

- CONOPS v1.2, sections 9.2 and 9.3, and lines 1194-1208 and 2162-2169.
- The [degraded-mode packet][degraded], its [prototype][prototype] and the
  [detection sweep][sweep].
- FML-ADR-071 and FML-ADR-087.

## 9. Owner disposition

*Awaiting the Owner.*

[degraded]: 2026-10-18-degraded-mode-when-no-safe-authority-decision-packet.md
[prototype]: 2026-10-24-option-a-prototype-peer-mode-under-a-server-cut.md
[sweep]: 2026-10-25-partition-detection-threshold-sweep.md
