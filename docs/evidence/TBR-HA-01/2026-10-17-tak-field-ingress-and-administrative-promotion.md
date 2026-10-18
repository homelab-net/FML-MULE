# tak.field ingress, shared trust and administrative promotion on two nodes

**Tier: deferred (real-hardware bench result; formal `HARDWARE-VERIFIED` held).**
Held for the reasons `docs/evidence/TBR-RF-01/2026-10-11-two-node-80211s-batman-real-radio.md`
gives, unchanged. Real nodes, a real 802.11s mesh between them, and real TAK
servers; synthetic clients. It is node-local: no independent instrument observed
the traffic.

**Trade:** `TBR-HA-01`, and CONOPS sections 25 to 30.
**Date:** 2026-10-17, 22:39 to 23:31 MDT. **Taken by:** Cameron Zobrist, on the
mule bench, with Claude.
**Nodes:** `pi-mule-1` (backend `a`, mesh `10.42.0.1`) and `pi-mule-2` (backend
`b`, mesh `10.42.0.2`), Raspberry Pi 4B, `6.18.50+rpt-rpi-v8`, one 802.11s hop on
`wlan1` with `batman-adv` (`FML-ADR-053`), the link of the 2026-10-11 artifact.
**Software:** official TAK Server `5.8-RELEASE92` on each node (Temurin
`17.0.20.1`, PostgreSQL `18.6` with PostGIS `3.6.4`), installed by
`test/bench/tak-server-bench-install.sh`; HAProxy `3.0.11` as the ingress, by
`test/bench/tak-field-ingress.sh`; clients `test/bench/tak-probe.py`, Python
`3.13.5`. **Procedure:** `test/bench/tak-failover-campaign.sh phase1|phase2`.
**Clocks:** both NTP-synchronised, offsets +16 ms and -8 ms at the start.
**Power:** both nodes reported `throttled=0x50005` throughout.

## Why this exists

CONOPS 25 to 30 and SAD sections 11, 12 and 14 describe how a TAK service is
hosted: EUDs use one stable name, `tak.field`; each MULE's local ingress
forwards it to whichever host is currently authoritative; hosts share a trust
anchor so a move causes no client trust failure; and promotion happens only
when authority is safe, with administrative promotion as the mandatory
fallback. `FML-ADR-031` (ingress), `FML-ADR-049` (authority registry) and
`FML-ADR-071` (state boundary) are decided. Nothing had exercised them across
two hosts. The earlier artifacts in this directory measure supervision of
services **on one host**; this measures a move **between hosts**.

## What this does not establish

Read this first. Each limit is large.

- **No state moves.** Backend `b` has its own empty database. After promotion it
  serves, but it holds none of `a`'s state, so by CONOPS 28 it is
  non-authoritative. Every recovery time below is the **cold or unsynchronized
  recovery class** CONOPS 27 separates from the 60-second synchronized
  objective. Nothing here measures that objective.
- **Nothing reports authority.** No component tells a client or Team Lead that
  the promoted service is non-authoritative. CONOPS 28's indication is absent;
  this records the gap, it does not fill it.
- **Promotion is scripted, not decided.** The administrator is a script that
  promotes about one second after the fault. That measures the mechanism, not
  detection or human reaction. Automatic promotion stays `TBR-HA-01`'s open
  question and was not attempted.
- **The registry is a stub.** One file per node names the authority, applied to
  HAProxy through its runtime socket, and kept consistent by running the
  promotion on both nodes. It is not the `FML-ADR-049` Service Authority
  Registry.
- **Bench deviations.** A hosts entry stands in for the `dnsmasq` template, and
  the ingress listens on 18089 because the co-located TAK Server owns 8089.
- **Synthetic clients.** No phone or WinTAK went through `tak.field`.
- **The server is not the preferred one.** `FML-ADR-032` prefers OpenTAKServer.
  Results about the ingress and registry pattern transfer; results about start-up,
  readiness and stop time are this server's.

## Topology

```text
probe (pi-mule-1) --tak.field:18089--> HAProxy pi-mule-1 --+
                                                            +--> authoritative backend only
probe (pi-mule-2) --tak.field:18089--> HAProxy pi-mule-2 --+     (a: 10.42.0.1:8089 or
                                                                  b: 10.42.0.2:8089, over the mesh)
```

Each ingress defines both backends and enables only the one the registry names.
HAProxy health checks report liveness and **never move traffic**: CONOPS 29
forbids uncontrolled competing authority.

## Phase 1: name, trust, routing

| Test | CONOPS / SAD | Result |
| --- | --- | --- |
| `tak.field` resolves to the local ingress on both nodes; both registries name `a` | 25.1 | **pass** |
| One client certificate from the shared CA, directly to each backend over the mesh | 25.3, 26.1; SAD 11.3 | **accepted by both**, no disconnect |
| Each server presents its own certificate (`CN=takserver`, `CN=takserver-b`), both issued by `FML-BENCH-TAK-CA` | SAD 11.3 | **pass**; the CA private key never left `pi-mule-1` |
| A client certificate from a foreign CA, to each backend | 25.3 control | **refused** 15 of 15 times on each |
| Both servers running, authority `a`, sender on `pi-mule-2` and receiver on `pi-mule-1`, 90 s, through `tak.field` | `FML-ADR-049`; 29 | `a` held sessions from **both** ingresses, one across the mesh; `b` held **none** while healthy; **89** of the sender's reports received, no disconnect |

The shared-trust result is the one the default deployment cannot give:
`docs/evidence/TBR-TAK-01/2026-08-31-shared-credentials-across-mules-and-euds.md`
measured that two independently installed servers generate independent CAs, so
a client enrolled on one fails on the other.

## Phase 2: administrative promotion

Each trial faults the authoritative backend, promotes the other on both
ingresses, and reads recovery from the receiver's log as the first report from
the sender after the fault. A partition rejects TCP 8089 from mesh sources on
the faulted node, so the server process stays alive but unreachable from the
mesh. Run in full twice.

| Trial | Fault | Promotion landed | Run 1 | Run 2 |
| --- | --- | --- | --- | --- |
| 1 | partition `a`, promote `b` | +0.7 to 1.2 s | **2.18 s** | **15.26 s**, see below |
| 2 | partition `b`, promote `a` | +1.1 to 1.3 s | **4.81 s** | **4.30 s** |
| 3 | partition `a`, promote `b` | +0.7 to 1.2 s | **4.30 s** | **4.80 s** |
| 4 | partition `b`, promote `a` | +0.6 to 1.1 s | **2.18 s** | **2.52 s** |
| 5 | partition `a`, promote `b` | +0.6 to 1.1 s | **2.32 s** | **2.20 s** |
| 6 | partition `b`, promote `a` | +1.1 to 1.3 s | **4.15 s** | **4.52 s** |
| 7 | planned switchover `a` to `b`, no fault | +0.6 to 1.1 s | **2.17 s** | **2.33 s** |
| 8 | process stop on `b`, promote `a` | +12.1 s | **10.2 s** outage | **10.7 s** outage |

**Every trial recovered with no client change.** Across the eleven partition
trials with a ready standby, recovery ran from **2.18 to 4.81 s**, median
**4.15 s**.

### Why the partition trials fall into two groups

Six trials took 2.2 to 2.5 s and five took 4.2 to 4.8 s, and the sender's log
separates them exactly. A trial is slow when the sender's **reconnect** lands
before its own ingress has promoted: it reports a position into the fault
(`closed by peer`), retries 0.5 s later into the still-enabled faulted backend,
waits out its own 3-second handshake timeout, and only then reaches the promoted
one. In run 1, trial 3 disconnected at +0.06 s and retried at +0.56 s, before
its ingress promoted at +0.71 s: slow. Trial 1 disconnected at +0.49 s and
retried at +0.99 s, after promotion at +0.68 s: fast. In the remaining fast
trials the disconnect coincides with the promotion itself, which is the
promotion cutting the session (+0.55 s against +0.56 s, +0.69 s against
+0.70 s). All twelve fault trials follow the rule.

So recovery after an administrative promotion is **promotion latency plus the
client's own retry behaviour**. An ATAK client's retry timing would set this for
a real phone, and was not measured.

Enabling the new backend before cutting the old was tried in run 2 and made no
measurable difference, so the ingress was returned to cutting first: that order
never has two backends enabled at once.

### A backend can be listening and not ready

Run 2's first trial took **15.26 s**. Backend `b` had been restarted nine
minutes earlier, had opened 8089 about a minute before the trial, and passed
HAProxy's TCP health check, but after promotion it accepted the clients' TLS
sessions and did not relay the sender's reports to the receiver for about
thirteen seconds. That is the distinction
`FML-ADR-049` draws, *"A process that is alive but does not hold authoritative
state is not an acceptable backend"*, measured: a port-level health check would
have called it ready. A registry has to ask the service whether it can serve,
not whether its port is open.

### A demoted server keeps serving the clients that bypass the ingress

The soak client and WinTAK reached `pi-mule-1`'s server by address, not through
`tak.field`. They stayed connected through every trial, and that is the
problem. Counting the probe sender's reports that reached the soak client in
each window after a promotion:

| Authority after the trial | Windows | Probe reports reaching the address-pinned client |
| --- | --- | --- |
| `a`, the server it was pinned to | 8 | **47 to 58** per window of about a minute |
| `b` | 8 | **0** in every window |

While `b` was authoritative there were two live islands: the `tak.field`
clients on `b`, and the address-pinned clients on the demoted `a`, each
accepting traffic and neither seeing the other. Demotion is an ingress state; the
demoted server is never told and keeps serving anyone who reaches it directly.
That is the *"uncontrolled competing authoritative stateful services"* CONOPS 29
forbids, reached through a path the ingress does not control. Two conclusions
follow, neither implemented here:

- **Every EUD has to reach TAK through `tak.field`.** A client configured with a
  server's address does not follow promotion, which is what CONOPS 25 already
  requires; this measures what violating it costs.
- **A demoted server has to be fenced, not only unrouted.** Promotion has to stop
  the old authority accepting clients by any path, or a partition heals into
  divergent databases.

### Process death is slower than partition

Stopping this server's five JVMs took about twelve seconds, and clients lost
service for 10.2 and 10.7 s. Promotion was scripted to follow the stop, so it
landed at +12.1 s; most of the outage is the stopping process no longer serving
while it shuts down. A real failure gives no such notice.

## Instrument faults, recorded

- **The first phase 1 run measured nothing for routing.** Its two probes ran
  one after the other, not together, because the launcher backgrounded a
  `cd && python3` list whose subshell held the ssh channel open. Fixed and
  rerun; the table above is the rerun.
- **A smoke test after the probes were refactored for lint counted 59 reports
  in 30 s from a one-per-second sender.** A sender from the previous run was
  still alive with the same identity. With it stopped, the committed probe
  received 30 in 30 s.
- **2026-10-17's earlier bench work found `ping -i 0.02` stalls on these
  nodes.** This campaign uses no ping; the probes log every connect and
  disconnect with a timestamp.

## What CONOPS 25 to 30 now have

| Section | State |
| --- | --- |
| 25 stable service identity; movement without EUD changes; compatible trust | **shown** with synthetic clients across two nodes |
| 26 state classes | common trust shown; mission-critical state **not moved** |
| 27 recovery | administrative, **cold class only**: 2.2 to 4.8 s partition, 10 to 11 s process death, 15 s into a not-ready standby. The synchronized 60-second objective is **not measured** |
| 28 authoritative indication | **absent**; recorded as a gap |
| 29 no competing authority | held **through the ingress** only: one backend enabled at a time, health checks never move traffic; **violated for address-pinned clients**, who stayed on the demoted server as a second island |
| 30 administrative promotion | **mechanism shown**, scripted |
| 31 service-host burden | see `docs/evidence/TBR-COMP-01/2026-10-17-official-tak-server-on-a-pi-4.md` |

`TBR-HA-01` stays `OPEN`. Its question, the simplest safe **automatic**
mechanism, is unanswered here; this shows that the routing half of any answer
works on these nodes and how long a client takes to follow it.

## Left running

Both TAK Servers, both ingresses with authority `a`, and the registry files.
`tak-field-ingress.sh down` removes the ingress; the TAK Servers can be stopped
with `systemctl stop takserver`.
