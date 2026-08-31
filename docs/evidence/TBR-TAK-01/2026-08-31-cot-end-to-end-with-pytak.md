# CoT end to end, with PyTAK

**Trade:** `TBR-TAK-01`.
**Date:** 2026-08-31.
**Taken by:** Cameron Zobrist, on the lab development machine.
**Status of this artifact:** `SIMULATED`. Containers on a development machine,
a synthetic client, no MULE hardware and no real device.

## What this supplies

A connected client, which every remaining outstanding item needed. `FML-ADR-033`
makes **PyTAK** the preferred library for custom CoT clients, so the client is
PyTAK rather than a hand-rolled socket.

It answers outstanding item 3 and partly opens item 5.

## Finding 1: OpenTAKServer is three processes, and upstream's container runs one

The package declares three console scripts:

```text
opentakserver = opentakserver.app:start
eud_handler   = opentakserver.eud_handler.eud_handler:main
cot_parser    = opentakserver.cot_parser.cot_parser:main
```

`opentakserver` is the web application and API. **`eud_handler` is the CoT
listener** that binds the TCP, SSL and UDP streaming ports, and `cot_parser` is
the worker that turns received CoT into rows.

Upstream's Dockerfile ends `ENTRYPOINT ["opentakserver"]`.

Measured: with only that process running, the listening sockets are
`127.0.0.1:8081` and nothing else. `OTS_ENABLE_TCP_STREAMING_PORT` is `True` and
`OTS_TCP_STREAMING_PORT` is `8088`, and **8088 does not appear**. Starting
`eud_handler` as its own process brings up `0.0.0.0:8088` immediately.

**A container built from upstream's own Dockerfile accepts no TAK clients.** It
serves an API and a web UI, and no ATAK, iTAK, WinTAK or PyTAK can connect to
it.

For this program that is a service-plane fact, not a curiosity: the TAK service
is **three units**, which bears on `services/quadlets/` conventions,
`FML-ADR-035` service control, dependency ordering, and `TBR-COMP-01`, which
must budget three Python processes rather than one.

## Finding 2: a default administrator account with the password `password`

`opentakserver/app.py`, on first start:

```python
logger.info("Creating administrator account. The password is 'password'")
app.security.datastore.create_user(
    username="administrator",
    password=hash_password("password"),
    roles=["administrator"],
)
```

This is an account, not a configuration default. It joins `OTS_CA_PASSWORD`
defaulting to `atakatak` and `OTS_RABBITMQ_PASSWORD` defaulting to `guest`,
recorded in `2026-08-31-durable-state-outside-the-database.md`.

`THREAT_MODEL.md` makes physical capture an expected condition and names the
opportunist as the most likely adversary "by a wide margin". A node shipped with
this account is a node whose administrator credential is in the upstream source.

Changing it is trivial. **Knowing to** is the point, and an image build that does
not is one nobody notices.

## Finding 3: the path works end to end

PyTAK sending five CoT position events to `tcp://127.0.0.1:8088`:

```text
cot     rows: 5
points  rows: 5
euds    rows: 1     FML-BENCH-2b9459e2 | FMLBENCH0 | fml-bench
```

So `PyTAK -> eud_handler:8088 -> RabbitMQ -> cot_parser -> PostgreSQL` carries a
position report from a client to durable storage, and **the EUD registers itself
on connection** without enrollment.

That last point is worth holding onto: an `euds` row appeared for a client that
presented no certificate, because the plain TCP streaming port does not require
one. `FML-ADR-038` selects EAP-TLS for production EUD admission, and this shows
what the unauthenticated port does in its absence.

## Finding 4: outstanding item 3, answered for the PLI path

> **Inspect durable queues** for sole-copy mission-critical items.

With a client connected, RabbitMQ holds exactly one queue:

```text
name         durable   messages
cot_parser   false     0
```

**It is not durable, and it carries CoT**, which the classification puts in
CONOPS 26.3, reconstructable. A broker restart loses whatever is in flight, and
what is in flight is position reports that connected clients republish.

So for the position path the answer is: **no durable queue holds the sole copy
of anything mission-critical**, because the only queue is non-durable and its
contents are reconstructable by design.

**That is not the whole of item 3.** Six durable *exchanges* exist -- `dms`,
`chatrooms`, `missions`, `groups`, `cot_parser`, `firehose` -- and no queue was
bound to `dms`, `chatrooms` or `missions` here, because a single client sending
PLI exercises none of those flows. Direct messages, chat and DataSync are
exactly the traffic most likely to exist only in transit, and they remain
untested.

## What this does not establish

**Items 4, 5 and 6 remain.** The different-node restore, the four workflow tests
in full, and the cache question. This exercised the PLI flow only.

**No certificate enrollment was performed**, so the certificate workflow test is
untouched and the observation about unauthenticated registration is a
description of the plain port rather than a test of the enrolled one.

**One client, five events, an empty database, one machine.** Nothing here
observed contention, volume, partition, or a restart.

**Not rootless**, and no compute measurement, so `TBR-COMP-01` gains nothing
from this beyond the process count in Finding 1.
