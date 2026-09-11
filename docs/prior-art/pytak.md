# PyTAK

**Evaluated:** 2026-09-10 at release `v7.6.1`, commit
`8ee576b0c5bf691addee425633e7dacdfee7c1f7`. **Verdict:** adopt within the
existing `FML-ADR-033` decision, while pinning each consumer and keeping the
upstream-first integration order from `FML-ADR-048`.

## Fit

PyTAK is a Python asyncio library and command-line client for sending and
receiving Cursor on Target. It supports XML and optional protobuf CoT across
TCP, TLS, UDP, files, console output, WebSockets, the Marti REST API and optional
MQTT. It can also enroll certificates and generate TAK data packages.

Those functions fit the standard TAK path and support `FML-REQ-018` and
`FML-REQ-029`. `FML-ADR-033` already selects PyTAK as the preferred custom CoT
transport and gateway library only where an upstream integration is
insufficient. This intake does not authorize a parallel gateway or custom CoT
vocabulary.

## Runtime and data

PyTAK normally runs as an ordinary user inside an owning client or gateway. Its
endpoint comes from `COT_URL`; it does not need an inbound listener in that
role. Security depends on the chosen transport. TLS can use PEM or PKCS12 client
material, enrollment uses a user and token, MQTT can add broker credentials, and
plain TCP or UDP offers no authentication.

Pinned Marti, WebSocket and MQTTS source disables server-certificate verification
when no client certificate is configured; CA material alone does not prevent
the fallback. Those paths block FML profile approval until explicit client and
server trust material is configured.

Version 7.6.1 caches enrolled PKCS12 material, its passphrase and a server
fingerprint under the invoking user's `.pytak/certs` directory. That cache is a
credential-bearing persistence boundary, not merely transient transport state.
An approved consumer profile owns and protects it through the enclosing service
rather than treating the library as stateless.

Package metadata is inconsistent: one field says Python 3.7 or later while
`python_requires` says 3.6 or later and below 4. FML should use the stricter
declared minimum until the supported range is resolved upstream.

## Intake result

- License: Apache-2.0, with the bundled `asyncio_dgram` module under MIT.
  Optional cryptography, protobuf, HTTP and MQTT dependencies require review for
  each selected consumer profile.
- Maintenance: five most recent releases span 2026-08-10 through 2026-08-23;
  v7.6.1 was also default-branch head when inspected. There were 20 open issues
  on 2026-09-10. Contributor totals are heavily concentrated in one maintainer.
- Platform: the pure-Python core declares POSIX, macOS and Windows support;
  optional native dependencies remain host dependent.
- Resources: not measured for an FML gateway profile.
- Security: GitHub published no repository advisory through its advisory
  endpoint on 2026-09-10. No independent audit or repository SBOM was identified;
  the no-certificate TLS fallback still requires an explicit FML control.
- Prototype: exact 7.6.1 was not run in this intake. Earlier FML end-to-end
  evidence used PyTAK but did not record its version, so it cannot qualify this
  release.

## Exit strategy and questions

Keep PyTAK behind protocol-level CoT and transport contracts so a direct
standards-compatible implementation can replace it. Each approved consumer pins
an exact version, selects only required optional dependencies, protects cached
credentials, and re-exercises its CoT path when that pin changes.

## Sources

- [Pinned README](https://github.com/snstac/pytak/blob/8ee576b0c5bf691addee425633e7dacdfee7c1f7/README.md)
- [Pinned package metadata](https://github.com/snstac/pytak/blob/8ee576b0c5bf691addee425633e7dacdfee7c1f7/setup.cfg)
- [Pinned transport implementation](https://github.com/snstac/pytak/blob/8ee576b0c5bf691addee425633e7dacdfee7c1f7/src/pytak/classes.py)
- [Pinned enrollment and certificate cache](https://github.com/snstac/pytak/blob/8ee576b0c5bf691addee425633e7dacdfee7c1f7/src/pytak/client_functions.py)
- [Earlier FML PyTAK evidence](../evidence/TBR-TAK-01/2026-08-31-cot-end-to-end-with-pytak.md)
- [Release history](https://github.com/snstac/pytak/releases)
- [Contributor summary](https://api.github.com/repos/snstac/pytak/contributors)
- [Repository security advisories](https://github.com/snstac/pytak/security/advisories)
