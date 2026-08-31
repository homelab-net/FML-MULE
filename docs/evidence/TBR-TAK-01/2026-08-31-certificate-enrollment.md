# Certificate enrollment, and a ten-year credential nobody checks

**Trade:** `TBR-TAK-01`.
**Date:** 2026-08-31.
**Taken by:** Cameron Zobrist, on the lab development machine.
**Status of this artifact:** `SIMULATED`. Containers on a development machine.

## What this supplies

The **certificate** test of the four SAD section 30.2 names in this trade's
closure evidence. `2026-08-31-mission-api-and-the-header-that-authenticates.md`
showed what the header path accepts; this is the enrolment flow that produces
what it accepts.

## Enrollment works

`GET /Marti/api/tls/config` with HTTP Basic authentication returns the
certificate configuration. `POST /Marti/api/tls/signClient/v2?clientUid=...`
with a CSR in the body returns `200` and a JSON document with three keys:
`ca0`, `ca1` and `signedCert`.

Basic authentication rather than the session flow, because the source says so:
"flask-security's `http_auth_required()` decorator will deny access because ATAK
doesn't do CSRF, so we handle basic auth ourselves".

**The credential used was `administrator` / `password`**, upstream's default,
which is enough to enrol a certificate.

The issued certificate verifies against the server's CA and a row appears:

```text
common_name        callsign   username   eud_uid
fmlbench-enrolled  (null)     (null)     FML-ENROLL-01
```

## Three findings, and they compound

### 1. The certificate is not bound to a user

`callsign` and `username` are null. The row records the `clientUid` and nothing
about who holds it.

Presenting the freshly enrolled certificate on the header path gets **past**
certificate verification and then fails inside authorisation:

```json
{"error": "'NoneType' object has no attribute 'has_role'", "success": false}
```

The certificate authenticated. There is no user behind it for `has_role` to
consult, so authorisation dereferences `None`. **Enrolment produces a credential
the server trusts and cannot attribute.**

### 2. Issued certificates are valid for ten years

```text
notBefore=Aug 31 21:44:50 2026 GMT
notAfter=Aug 28 21:44:50 2036 GMT
```

`OTS_CA_EXPIRATION_TIME` defaults to `3650` days and applies to issued client
certificates, not only the CA.

CONOPS plans **volunteer-owned** EUDs. A decade is longer than most volunteers
stay, longer than most phones last, and far longer than the interval at which a
device is lost, sold or handed on.

### 3. Revocation is not consulted on the header path

`ca/ca.crl` exists on disk, 638 bytes, maintained beside the CA. The
verification path does not load it:

```text
store = crypto.X509Store()
store.add_cert(ca_cert)
ctx = crypto.X509StoreContext(store, cert)
ctx.verify_certificate()
```

The store receives the CA certificate and nothing else. There is no
`add_crl()` and no `X509StoreFlags.CRL_CHECK`, so a revoked certificate that
still chains to the CA verifies exactly as an unrevoked one does.

### What the three make together

A certificate that:

- authenticates on **possession of public data**, because the header carries no
  proof of the private key;
- is valid for **ten years**;
- and is **not checked against the revocation list** that exists on disk.

`THREAT_MODEL.md` records that "credential revocation in a disconnected network
is hard and its effectiveness is `TBD`", and that a revoked credential should be
assumed usable on a partition that has not learned of the revocation. **On this
path it is usable on a node that has learned**, because the node does not look.

The 2026-08-27 analysis's Finding 2 was that losing revocation state fails open.
It is stronger than that: on this path, revocation state is not consulted, so
losing it changes nothing because having it changes nothing.

## The three findings chain into an authentication bypass in the selected software

**Added 2026-08-31.** This is upstream `OpenTAKServer` default behaviour, on a
node this program has not deployed, recorded so that `services/ingress/` and
`FML-ADR-038` constrain it before anyone does. It is described at the level of
mechanism, not as a procedure.

The Mission API derives the acting user from the certificate:

```text
username = cert.get_subject().commonName
user = app.security.datastore.find_user(username=username)
```

**The certificate's Common Name becomes the identity.** Combined with the three
findings above:

- Enrollment signs whatever CN the CSR carries. A CSR with `CN=administrator`
  produces a certificate for `administrator`.
- Enrollment requires only a valid account and its password, with **no role
  check** in `basic_auth`. Any account, including a low-privilege one, can enrol.
- The header path authenticates on the certificate alone, with no proof of
  possession.

Demonstrated end to end: a certificate enrolled with `CN=administrator` and then
presented in the `X-Ssl-Cert` header, **with no private key and no password**,
returns a successful Mission API response as `administrator`.

So the chain is: a valid low-privilege account enrols a certificate naming a
higher-privilege user, and that certificate authenticates as the named user on
the API path. **The mitigation is entirely at the reverse proxy**, which is why
`services/ingress/` now carries the requirement that the proxy set the header
from a real client-certificate handshake rather than trust the application port,
and why `THREAT_MODEL.md` records the certificate as weaker than it looks.

This has not been reported to the OpenTAKServer project. Whether to do so, and
on what timeline, is a Program Owner decision recorded in the follow-up rather
than taken here.

## What this does not establish

**This is `verify_client_cert()`, used by the Marti API paths.** The SSL
streaming port performs a real TLS handshake, which does prove possession, and
may consult revocation differently. **That was not tested**, and the finding
must not be read as covering every path into the server.

**The revoked-certificate test could not be run, because nothing revokes.**
This artifact first said the conclusion was read from absent CRL loading rather
than from revoking a certificate. Checked on 2026-08-31: there is no revocation
path at all. No code calls `openssl ca -revoke`, there is no `revoke_certificate`
or `def revoke`, the generated `ca.crl` reads "No Revoked Certificates", and
`crl_index.txt`, the CA database that would list them, is zero bytes. So a
certificate cannot be revoked in the first place, which is a stronger statement
than "revocation is not consulted": there is nothing to consult and no way to
put anything in it.

**No fix is proposed.** How MULE terminates TLS, whether it sets rather than
forwards `X-Ssl-Cert`, what certificate lifetime it configures, and how it binds
a certificate to a user are `services/ingress/`, `FML-ADR-038` and `TBR-ID-01`
questions. This artifact reports what upstream does by default.

**The default administrator credential was used to enrol.** Whether a
non-administrator account can is untested.
