# Service-plane steady-state memory footprint

**Tier:** `SIMULATED`. The x86 dev host, a running reference deployment, steady
state, no load injected, and no network plane co-resident. It is the "size" half
of the budget, not the budget.

**Date:** 2026-09-06. **Node:** development machine (see `docs/dev-machine.md`),
`6.12.105+deb13-amd64 x86_64`, rootful `podman`, cgroups v2. **Instrument:**
`podman stats --no-stream` (each container's cgroup `memory.current`).
**Configuration:** the persistent `fml-*` reference service-plane deployment,
warmed for ~2 days: OpenTAKServer 1.7.13 (three processes) on `python:3.12`,
RabbitMQ, PostGIS 16-3.4, and nginx fronts. **Procedure:**
`test/bench/service-plane-footprint.sh`. **Taken by:** Cameron Zobrist.

## What this settles

`TBR-COMP-01` is CRITICAL and its dependency `TBR-TAK-01` is now `CLOSED`, so its
software half is bankable. SAD section 25.3 requires an explicit compute/memory
model, and the host is not selected until the resource and power models agree.
`FML-ADR-021` accepted that the service plane can starve the routing daemon; the
reserve that bounds that has to be set against a measured service-plane size.
This is that measurement's size half.

## The measurement

Steady-state resident memory, stable across repeated samples:

```text
  fml-ots               178.5 MB    OpenTAKServer API (opentakserver)
  fml-eud_handler       115.4 MB    CoT streaming handler
  fml-cot_parser        242.5 MB    parse/persist worker
  fml-mq                 97.7 MB    RabbitMQ (broker)
  fml-pg                  9.6 MB    PostGIS (see caveat)
  fml-nginx-tls           2.5 MB    ingress (TLS)
  fml-nginx-api           2.5 MB    ingress (API)
  fml-tiles               2.0 MB    static tile front (nginx)
  ------------------------------------------------------------
  AGGREGATE            ~650  MB
```

**The service plane sizes at ~650 MB resident at idle steady state**, and it is
dominated by OpenTAKServer: its three processes total ~536 MB, with `cot_parser`
(~243 MB) the single largest, then RabbitMQ at ~98 MB. Everything else -- the DB
at idle and the three nginx fronts -- is under 20 MB combined. This is the
figure a catalog resource envelope and the CM4 memory-class decision are set
against.

**OpenTAKServer is three processes, made visible here.** The API, the CoT
streaming handler, and the parse/persist worker each run as their own process;
`tak-state.sh` records that upstream's single-entry Dockerfile runs only the
first, which is why a naive one-process deployment silently loses the CoT path.
The budget must carry all three.

## What this is not

- **Not the CM4 footprint.** x86 only -- the size half. The arm64/CM4 resident
  figure and CPU under load are `TBR-COMP-01`'s hardware item and stay open. This
  selects no host and states no 4 GB-versus-8 GB verdict; it gives the number
  that decision is made against, alongside the power model.
- **Not a peak.** No load was injected, to avoid disturbing a live deployment.
  The peak under a client association storm and a CoT flood -- which SAD 25.3
  lists -- needs the network plane co-resident and radios, and is not here.
- **PostGIS at idle understates the DB.** Its ~9.6 MB is idle-resident; shared
  buffers are allocated lazily, so under query load the DB footprint grows toward
  `shared_buffers`. Treat 9.6 MB as a floor, not the DB's budget.
- **The tile front here is nginx (~2 MB), not the selected server.** The selected
  tile server is Martin (`FML-ADR-073`), separately measured at ~8.5 MB idle /
  ~28 MB under load (`docs/evidence/TBR-MAP-01/2026-09-06-martin-mbtiles-server-footprint.md`).
  The service plane with Martin substituted is ~657 MB, within rounding of the
  figure above.
- **Not the reservation mechanism.** Whether the network-plane reserve is a
  systemd limit, a dedicated core, or priority (SAD 10.4) is a design item this
  size figure informs but does not settle.

## What this unblocks

The service-plane size -- the largest missing half of `TBR-COMP-01`'s software
work -- is now measured: ~650 MB, OTS-dominated. It directly informs the CM4
memory class (the Bank C BOM decision) and gives every service catalog entry a
basis for its resource envelope. What remains for `TBR-COMP-01` closure is the
hardware half: the arm64/CM4 figure, CPU under load, and the peak under a
service-plane storm with the network plane co-resident.
