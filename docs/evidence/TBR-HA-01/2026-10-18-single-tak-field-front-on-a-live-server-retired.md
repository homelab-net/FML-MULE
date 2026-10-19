# A single `tak.field` front on a live server: what it showed, and why it was retired

**Tier: real-hardware bench result; formal `HARDWARE-VERIFIED` held** (see
`docs/evidence/TBR-NET-02/2026-09-27-one-lora-hop-to-a-partner-node.md` for why).
**Every timing figure is provisional:** both Pi nodes read `0x50005`
(under-voltage, throttled).

**What was built.** Bench mule1 already hosts a live OpenTAKServer for a pilot
group. On it, an nftables redirect sent every *new external* TCP connection to
port 8089 into HAProxy. HAProxy forwarded it by TCP passthrough to exactly one
backend:

- that host's own OpenTAKServer over loopback (the default);
- official TAK Server 5.8 on pi-mule-1;
- official TAK Server 5.8 on pi-mule-2.

Promotion was administrative: put the others into maintenance, cut their
sessions, enable the new backend. Clients kept one server setting throughout.

| Item | Value |
| --- | --- |
| Date | 2026-10-18, about 12:20 to 18:00 local |
| Taken by | Cameron Zobrist (the Program Owner), with Claude Code operating the bench at his direction |
| Clients | the owner's iTAK (iOS) over the tailnet, synthetic TLS EUDs, and the LoRa gateway of the same-date `TBR-NET-02` record |

## Shown

| What | Result |
| --- | --- |
| Promotion round trip | One name answered as each backend in turn within 2-3 s of the command. The backends were distinguished by their certificates' address SANs. |
| An iTAK client through the front | The owner's iTAK stayed connected, and its position and chat crossed onto LoRa through the gateway. |
| Clients and the gateway across three swaps | Both reconnected to each new backend in about 2.1 s, which is their retry delay. Delivery figures are in the `TBR-NET-02` record. |
| The live server unable to form an island | Every external 8089 connection entered the front, and the host's server was reachable only over loopback. So a demoted server could not keep address-pinned clients, **on port 8089 only**, and only because the live server hosted the front. |

## Findings

1. **The live server's certificate does not name `tak.field`.** OpenTAKServer
   presents `CN=opentakserver` with address SANs only. Clients that check the
   hostname cannot verify it as `tak.field`. The Pi TAK Servers' leaves name it.
   This bears on CONOPS 25's certificate expectation.
2. **The name does not move the other services.** Only 8089 was fronted. Data
   packages, the Marti API and enrollment go wherever each client was configured:
   the live server serves those on 443/8446 on its tailnet address, while the Pis
   serve 8443/8446. So continuity was shown for the CoT stream only.
3. **OpenTAKServer delivers nothing to a connection until it has seen that
   client's own SA.** Real clients send one at once; anything that doesn't loses
   traffic after every swap.
4. **A message in flight at a swap's hard cut is lost** (one in 61). GeoChat has
   no end-to-end acknowledgement. Open, for this trade.

## Why it was retired

The design worked, but it was the wrong design for this bench, on two counts:

- **It deviates from SAD §11.2 and `FML-ADR-049`.** Those put an ingress, and the
  registry's local view, on each MULE. A single front makes its host a single
  point of failure, and CONOPS 27 (failure of the active host) can't be exercised
  while front and default authority share one host.
- **It exposed a live server.** It redirected every external 8089 connection on a
  server with pilot users. A promotion would have moved those users onto bench
  servers holding none of their data, and bringing the front up reset their
  sessions.

**On 2026-10-18 the bench was isolated from that server:**

- the redirect, the front's unit and tool, and its HAProxy were removed;
- HAProxy and socat were purged, since neither was installed before;
- the server again answers 8089 directly, verified by a TLS handshake;
- the bench accounts created on it were **deactivated**, not deleted. Fourteen
  foreign keys reference its EUD table, so hand-deleting rows on a live server
  was the riskier change. The inert history rows remain;
- the bench-only tailnet grant, its route approval, and the desktop's advertised
  route were removed.

**The bench's authority set is now its own:** OpenTAKServer and TAK Server on the
Pis. Per-node ingress following one registry, with a partition mode, is the next
step, and it never touches the live server's 8089.

## What this does not establish

- Synchronized state: no state moves, so every figure is in the cold class.
- Automatic promotion.
- Any per-node-ingress behaviour.
- Swaps between like implementations. These swaps ran OpenTAKServer against TAK
  Server 5.8, so they don't meet CONOPS 26.1.

## Procedures

The front's tool was scratch tooling. It is not committed because it hard-coded
host interfaces and addresses, and it is superseded by per-node ingress.
`test/bench/tak-field-ingress.sh` remains the committed per-node ingress
procedure (see `2026-10-17-tak-field-ingress-and-administrative-promotion.md`).
