# No durable queue holds a sole copy, and chat reaches the database

**Trade:** `TBR-TAK-01`.
**Date:** 2026-08-31.
**Taken by:** Cameron Zobrist, on the lab development machine.
**Status of this artifact:** `SIMULATED`. Two synthetic PyTAK clients against a
containerised stack on a development machine.

## What this closes

Outstanding item 3 of the six the 2026-08-27 analysis listed:

> **Inspect durable queues** for sole-copy mission-critical items. Finding 3.

The previous artifact answered it for position reports and said plainly what it
had not covered: "no queue was bound to `dms`, `chatrooms` or `missions` here,
because a single client sending PLI exercises none of those flows. Direct
messages, chat and DataSync are exactly the traffic most likely to exist only in
transit, and they remain untested."

This exercises chat, with two clients.

## The exercise

Two PyTAK clients on `tcp://127.0.0.1:8088`, both registering by position
report, then a GeoChat message from one to the other in ATAK's own format:
`b-t-f` event, `__chat` with `chatgrp`, `remarks`, and a
`__serverdestination`.

## Chat reaches durable storage

```text
euds            rows: 2      FMLALPHA, FMLBRAVO
geochat         rows: 1      FML-A-40721b72 -> FML-B-6ec6cf65
                             remarks: "FML bench GeoChat probe"
chatrooms       rows: 1
chatrooms_uids  rows: 2
```

The message text is in the database. A chatroom was created and both
participants recorded in it, from a single directed message.

That confirms the classification in
`2026-08-31-relational-state-decomposed-into-conops-classes.md`, which put
`geochat` in CONOPS 26.2 as the coordination record and `chatrooms` and
`chatrooms_uids` in 26.1 as room structure. **The message and the room are
created by the same act and land in different classes**, which is the sort of
thing a classification is for.

## The answer: there is no durable queue at all

With two clients connected and chat delivered:

```text
name         durable   auto_delete   messages
cot_parser   false     false         0
```

Bindings, complete:

```text
source_name   destination_name   routing_key
              cot_parser         cot_parser
cot_parser    cot_parser         cot_parser
```

**One queue exists, it is not durable, and it is empty.** The six durable
exchanges recorded earlier -- `dms`, `chatrooms`, `missions`, `groups`,
`firehose`, `cot_parser` -- have **no queues bound to them** except the last.

An exchange with no queue bound to it stores nothing. A message published to it
is discarded, not retained. So:

**No durable queue holds the sole copy of any mission-critical item, because in
this configuration no durable queue exists.** Finding 3 of the 2026-08-27
analysis -- "a durable queue holding the only copy of a mission-critical item"
-- describes a hazard that this deployment does not have.

The path is `client -> eud_handler -> cot_parser queue -> cot_parser -> SQL`.
The queue is a work handoff between two processes on one host, not a store.
Losing it loses whatever is mid-flight, and mid-flight is measured in the time
one process takes to hand to another.

## What this does not establish, and one caveat matters

**The clients are PyTAK, not ATAK.** OpenTAKServer may bind per-client queues in
response to subscription behaviour that a real ATAK client performs and this
synthetic one does not. The finding is therefore precise about its scope: **in
this configuration, with these clients, no durable queue exists.** A real client
could produce different bindings, and that is worth checking when one is
available.

**DataSync and Mission API flows were not exercised.** The `missions` exchange
is durable and unbound here, and a mission created through the Mission API is
the case most likely to differ. That is part of outstanding item 5.

**Delivery to the second client was not verified.** The message reached the
database; whether the server forwarded it over the socket to `FMLBRAVO` was not
captured, and matters for a different question than this one.

**Items 4, 5 and 6 remain**: the different-node restore, the four workflow tests
in full, and the cache question.
