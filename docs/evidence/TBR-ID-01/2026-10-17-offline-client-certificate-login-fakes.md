# Offline client-certificate login against fakes, with no network but loopback

**Trade:** `TBR-ID-01`.
**Date:** 2026-10-17.
**Taken by:** Claude, for the Program Owner, on two hosts. **Instrument:**
`test/bench/browser-login-offline.py`, stdlib Python and the `openssl` CLI, run
inside an unprivileged network namespace (`unshare -rn`) that holds only
loopback.
**Status of this artifact:** `SIMULATED`. Every component is a fake: the
ingress is not HAProxy, the client is not a browser, and no EUD was involved.

**It does not close the trade**, and it does not select an approach. It
demonstrates option C of
`2026-10-17-authentication-events-with-and-without-a-common-idp.md` offline,
because the Closure evidence asks for offline login to be demonstrated and C is
the option that analysis recommends measuring next. Offline login for a
*selected* approach is still owed.

## Hosts

| Host | OS and kernel | Python | OpenSSL |
| --- | --- | --- | --- |
| Operator desktop, WSL 2 | Ubuntu 24.04.4 LTS, `6.6.87.2-microsoft-standard-WSL2+` x86_64 | 3.12.3 | 3.0.13 |
| `pi-mule-1` | Debian GNU/Linux 13 (trixie), `6.18.50+rpt-rpi-v8` aarch64 | 3.13.5 | 3.5.7 |

`pi-mule-1` matters because it is the program's Debian arm64 userland
(`FML-ADR-022`), and it found a defect the desktop did not; see below. No
timing is measured, so the bench's under-voltage throttling does not bear on
any result here.

## Procedure

```sh
unshare -rn sh -c 'ip link set lo up && \
    python3 test/bench/browser-login-offline.py --require-offline'
```

The script refuses to run unless the only interface up is loopback **and** a
connection to a public address fails with `ENETUNREACH`. That makes "no WAN" a
checked precondition rather than a description. It then builds, in a temporary
directory removed on exit:

- three throwaway authorities: a **mission client authority** (standing in for
  the `FML-ADR-036` mission/enrollment authority), a separate **ingress server
  identity** authority, as `services/ingress/README.md` requires (*"the CA that
  signs the ingress certificate must not be a CA that authenticates
  anything"*), and **another deployment's** authority;
- two-day client credentials, an expired one, a not-yet-valid one, one revoked;
- two fake nodes of one deployment. Node A holds the revocation list issued
  after the revocation. Node B holds the one issued before, standing in for a
  partition the revocation has not reached;
- role and scope data held apart from the certificates (SAD section 16.4).

No key or certificate left the temporary directory, and every identity is a
placeholder (`member-a1`, `lead-a`, `admin-1`).

## Result

With the committed script, **every run on both hosts was 20 of 20 as
expected: 12 consecutive runs on the desktop and 10 on `pi-mule-1`.** An
earlier version failed one case on one desktop run, and the reason is in the
section below; it was a defect in how the case was judged, not a refusal that
failed. Offline precondition as recorded on `pi-mule-1`:

```text
offline precondition: interfaces=['lo'] (only lo up); connect 1.1.1.1:443 -> ENETUNREACH
```

The WSL namespace also lists `sit0` and `tunl0`, both down, and the script
records them.

| Case | Outcome on `pi-mule-1` |
| --- | --- |
| Unit Member, own identity | `200 as member-a1` |
| Unit Member, own team's status | `200 as member-a1` |
| Unit Member, an administration function | `403 as member-a1` |
| Team Lead, another team's status | `403 as lead-a` |
| Field Network Administrator, an administration function | `200 as admin-1` |
| No client certificate | refused at TLS, the application not reached; see below for how the refusal surfaces |
| Valid certificate, absent from role data | `403` |
| Expired certificate | refused, `CERTIFICATE_EXPIRED` alert |
| Certificate not yet valid | refused, `BAD_CERTIFICATE` alert |
| Certificate from another deployment's authority | refused, `UNKNOWN_CA` alert |
| Forged principal header sent through the ingress | `403 as member-a1`: the header was replaced |
| **Control:** forged header, ingress bypassed | `200 as admin-1` |
| Revoked, at the node holding the revocation | refused, `CERTIFICATE_REVOKED` alert |
| Revoked, at the partition without it | `200 as member-revoked` |
| Same credential at the second node | `200 as member-a1` |
| Team scope added in role data, same certificate | `200 as lead-a` |
| Node time not credible | `503` from the ingress |
| Node time credible again | `200 as member-a1` |
| Not-yet-valid credential, verified at the true time | `certificate is not yet valid` |
| Same credential, verified with the clock two days fast | `verify OK` |

**No refusal reached the application.** The script counts requests the fake
application receives and turns any refusal that reached it into a miss, so
"refused" cannot be a refusal at the wrong layer.

### What each group shows

- **Authorization is not in the certificate.** Role and team scope come from
  data, and a scope change took effect on the certificate already held. That is
  SAD section 16.4, and it is why reissuing is not the way to change a role.
- **One credential works across a deployment's nodes** that share the mission
  authority, and not across deployments. `TBR-TAK-01` measured OpenTAKServer's
  default as the opposite: a certificate authority per node, so an EUD could not
  authenticate to the MULE beside its own.
- **Revocation lag is reproduced, not solved.** The partition without the
  revocation accepted the revoked credential. That is CONOPS section 15 item 4,
  and nothing in option C changes it.
- **The two time rows are the reason for the time gate.** OpenSSL judged the
  not-yet-valid credential against the clock it was given, and accepted it when
  the clock was two days fast. TLS cannot know its clock is wrong, so
  `FML-ADR-042`'s *"shall not fail open"* has to be enforced from the node's
  time-credibility state. The fake ingress does that with one check.
- **The control row is why backend isolation is a security control.** With the
  ingress bypassed, a forged header was accepted as an administrator.

## The cases discriminate

Three deliberate defects were introduced on the desktop host, one at a time,
against the committed script. Each was caught by exactly the case meant to
catch it and by no other:

| Defect | The case that failed | Observed |
| --- | --- | --- |
| Ingress forwards a client's principal header instead of setting it | forged header through the ingress | `200 as admin-1` |
| Revocation check removed | revoked, at the node holding the revocation | `200 as member-revoked` |
| Time gate removed | node time not credible | `200 as member-a1` |

The first is the `TBR-TAK-01` header bypass reproduced from the proxy side: a
Unit Member's request succeeded as an administrator.

## Two things the target userland found

**Python 3.13 verifies strictly by default.** The first run on `pi-mule-1`
failed every TLS case with the *client* refusing the fake ingress certificate.
Python 3.13 sets `VERIFY_X509_STRICT` in its default context, and the fake
certificates lacked key-identifier extensions and critical CA constraints,
which strict mode requires. The defect was in the fake PKI, not in the
mechanism, and it is fixed in the script. The desktop's Python 3.12 accepted
the under-specified certificates silently. The lesson for a real mission
authority is narrow and worth one line: it should issue certificates a strict
verifier accepts, because a client that tightens its defaults refuses the
rest.

**With no client certificate, the refusal surfaces three ways.** The server
closes the connection as it sends its `certificate_required` alert, and the
client reports whichever it reads first. On `pi-mule-1` that was a connection
reset on all 10 runs. On the desktop it was the alert on 9 of 12 runs and a TLS
EOF with no alert on 3. The script first expected the alert, then the alert or
a reset, and the EOF failed it once; it now accepts any TLS-level refusal for
that one case. That is not a loosening of the test: the application-reached
check is what establishes a refusal, and it held on every run. Every other
refusal carried its specific alert on every run on both hosts.

## What this does not establish

- **Anything about a phone.** Whether a mobile browser presents a client
  certificate silently, asks once, or asks per session is the measurement the
  analysis names as deciding between options B and C. A Python client presents
  its certificate with no prompt by construction, so this artifact counts no
  selection prompts and claims none.
- **Anything about HAProxy.** `FML-ADR-031`'s proxy was not run. Its
  client-certificate verification, revocation-list loading and header setting
  are the same mechanism in a different implementation, which is a reason to
  expect it works and not evidence that it does.
- **Signed role data.** The fake reads unsigned JSON. Signature verification
  belongs to the Mission Trust Service (`FML-ADR-047`), which is not built.
- **The time-credibility decision.** The fake ingress reads a boolean. Deciding
  it is `mule/timekeeping.py`'s, and the skew values are `TBR-TIME-01`'s.
- **Options A and B.** Neither was demonstrated.
