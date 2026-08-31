# The Mission API, and the header that authenticates without a key

**Trade:** `TBR-TAK-01`.
**Date:** 2026-08-31.
**Taken by:** Cameron Zobrist, on the lab development machine.
**Status of this artifact:** `SIMULATED`. Containers on a development machine.

## Why this was done early

`2026-08-31-no-durable-queue-holds-anything.md` closed outstanding item 3 and
named the case most likely to overturn it:

> The `missions` exchange is durable and unbound here, and a mission created
> through the Mission API is the case most likely to differ.

Running that test last would have looked like avoiding the one that breaks the
result. It was run first.

## Item 3 holds

With a mission created through the Marti Mission API:

```text
name         durable   auto_delete   messages
cot_parser   false     false         0

source_name   destination_name   routing_key
              cot_parser         cot_parser
```

**One queue, not durable, and the `missions` exchange still has nothing bound to
it.** The item-3 finding survives the test chosen to break it.

## Getting there produced three findings of its own

### 1. `X-Ssl-Cert` authenticates on a certificate alone

The Mission API refuses a plain request:

```json
{"error": "Missions are only supported on SSL connections", "success": false}
```

"SSL connection" is not what it sounds like. `verify_client_cert()` reads the
header named by `OTS_SSL_CERT_HEADER`, default `X-Ssl-Cert`, URL-decodes it,
loads it as a PEM certificate, and checks that it chains to `ca/ca.pem`:

Quoted verbatim, in a `text` block rather than a `python` one so that the
formatter does not rewrap somebody else's source:

```text
cert_header = app.config.get("OTS_SSL_CERT_HEADER")
if cert_header not in request.headers:
    return False
cert = crypto.load_certificate(crypto.FILETYPE_PEM, unquote(request.headers.get(cert_header)))
...
ctx.verify_certificate()
```

It verifies that the certificate is **valid**. It does not verify that the
sender **holds the private key**, because a header cannot: that is what a TLS
handshake is for, and this design moves the handshake to a reverse proxy and
carries only its conclusion.

**Demonstrated:** a client certificate was issued from the server's own CA and
presented in the header **with no private key and over plain HTTP**. The Mission
API accepted it and moved on to validating the `creatorUid`.

**A certificate is public data.** Anyone holding a copy of a valid client
certificate — from a packet capture, a shared device, a backup, a lost EUD — can
present it in this header and be authenticated as its subject, if they can reach
the application port.

The mitigation upstream ships is that `OTS_LISTENER_ADDRESS` defaults to
`127.0.0.1`, so only a local proxy can reach it. **That mitigation is a default
this program can break without noticing**: `FML-ADR-029` puts services in
containers, and the bench used `--network host` precisely because it was
convenient. A published port, a bridge network, or a proxy that forwards rather
than sets `X-Ssl-Cert` all remove it.

`FML-ADR-038` selects EAP-TLS for EUD admission and `TBR-ID-01` asks about a
common identity provider. **This is a third authentication path** and neither
covers it.

### 2. The CA key opens with the documented default

The client certificate above was signed using `ca-do-not-share.key` with
`-passin pass:atakatak`, which is `OTS_CA_PASSWORD`'s default. That was recorded
from source in `2026-08-31-durable-state-outside-the-database.md` and is now
demonstrated: **the default password opens the certificate authority.**

Anyone with the data folder can issue certificates the server will trust.

### 3. The Mission API reported failure and created the mission

```json
{"error": "Failed to add mission: 'NoneType' object has no attribute 'id'", "success": false}
```

After that response:

```text
missions         rows: 1     FMLBENCHMISSION | public | FML-BENCH-62b185e6
mission_changes  rows: 1
mission_roles    rows: 1
mission_uids     rows: 0
```

**The mission exists.** The call reported failure after writing three tables,
which is a partial write reported as a failure. An operator who retries gets
either a duplicate or an error about one, and an operator who does not retry has
a mission they were told they do not have.

This is upstream behaviour on a `tool=public` mission created without an ATAK
client, so it may not occur on the path a real client takes. It is recorded
because the state study is about what survives, and a row written during a call
reported as failed is a row nobody knows is there.

## What this does not establish

**Not the whole of item 5.** DataSync content, mission packages, certificate
enrollment through the proper flow, and the map cache are still untested. This
exercised mission creation only.

**No real client.** The certificate was presented by `curl`, not by ATAK through
a reverse proxy, and the mission was created without one. Whether a real client
produces different queue bindings is still open, and remains the standing caveat
on item 3.

**The `NoneType` error was not diagnosed.** Whether the mission is fully usable,
or was left half-created in a way that matters, is not established here.

**No fix is proposed for the header path.** Whether MULE terminates TLS at a
proxy, and how it guarantees `X-Ssl-Cert` is set rather than forwarded, is a
`services/ingress/` question this artifact raises and does not answer.
