# openmanetd

**Evaluated:** 2026-09-10 at release `1.3.10`, commit
`beaf76c54b65cbaba7b998d1f7bacf9c35f5c6a1`. **Verdict:** retain as
pattern-only telemetry and management prior art and as a permitted prototype;
do not adopt it into the production node at this stage.

## Fit

`openmanetd` is a Go daemon with an embedded web application and ConnectRPC API.
It manages batman-adv and Alfred data, radios, DHCP, network interfaces, VXLAN,
Tailscale, GNSS, CoT and optional audio. It therefore bears directly on
`FML-REQ-011`, `FML-REQ-012`, `FML-REQ-017`, `FML-REQ-022` and
`FML-REQ-032`.

The pinned release exposes its API on port 8087 and a frontend on port 8081. It
stores configuration and SQLite data under `/etc/openmanetd`, uses PAM-backed
sessions, and can use TLS certificate and key paths. The pinned runtime source
sets authentication enabled when `auth.enable` is absent. The pinned
authentication guide contradicts that code by calling disabled the default and
also states that a fresh node starts as root with no password. Runtime source
governs, and the credential bootstrap still needs prototype verification. The
daemon's purpose requires authority over radio, interface, DHCP, route,
service-restart and reboot operations.

That breadth does not fit as a quiet production dependency. `FML-ADR-023`
permits `openmanetd` as a prototype and telemetry reference, while
`FML-ADR-027` forbids assuming that it supplies deterministic coexistence scan
or transmit-suppression primitives. Adopting its API would also decide open
service and radio-control trades before their evidence exists.

## Reusable work

The reusable material is the implementation pattern and prototype surface:

- narrow readers for batman-adv, Alfred, GNSS and interface state;
- a documented ConnectRPC schema and frontend-only development mode;
- SQLite-backed local state and optional instrumentation snapshots; and
- a comparative way to inspect OpenMANET behavior without making the daemon the
  production control plane.

Any later direct reuse requires a new review of API scope, least privilege,
authentication defaults and its relationship to the MULE placeholder services.
No `openmanetd` interface is adopted by this evaluation.

## Intake result

- License: GPL-3.0; linking or incorporating code requires license review.
  Bundled dependency review remains pending.
- Maintenance: five releases were published between 2026-08-09 and
  2026-08-16, and later commits exist. GitHub's contributor summary is heavily
  concentrated in one maintainer account.
- Platform: Linux/OpenWrt nodes; the full build uses CGO, SQLite, audio and
  other native libraries, while a lite build omits audio hardware dependencies.
- Resources: not measured.
- Data: YAML configuration, SQLite state, protobuf/JSON RPC messages, CoT/NMEA
  output and optional JSON instrumentation snapshots. No backup or migration
  contract was identified in the pinned documentation.
- Security: no repository security advisory was published through GitHub's
  advisory endpoint on 2026-09-10. No independent audit or repository SBOM was
  identified in the pinned artifact.
- Prototype: not run in this intake. Frontend-only mode provides a later
  non-hardware prototype path; privileged management needs an isolated bench.

## Exit strategy and questions

Keep the pinned source as a comparison point and implement no production
dependency. If a later trade approves a narrow reuse, wrap only the approved
surface behind a MULE-owned interface and retain a replacement path. The open
questions are whether any reader saves more maintenance than a direct kernel or
service interface and which, if any, control endpoints are both supported and
least-privilege compatible.

## Sources

- [Pinned README](https://github.com/OpenMANET/openmanetd/blob/beaf76c54b65cbaba7b998d1f7bacf9c35f5c6a1/README.md)
- [Pinned authentication guide](https://github.com/OpenMANET/openmanetd/blob/beaf76c54b65cbaba7b998d1f7bacf9c35f5c6a1/docs/api-authentication.md)
- [Pinned configuration defaults](https://github.com/OpenMANET/openmanetd/blob/beaf76c54b65cbaba7b998d1f7bacf9c35f5c6a1/internal/config/config.go)
- [Pinned example configuration](https://github.com/OpenMANET/openmanetd/blob/beaf76c54b65cbaba7b998d1f7bacf9c35f5c6a1/example_config.yml)
- [Release history](https://github.com/OpenMANET/openmanetd/releases)
- [Contributor summary](https://api.github.com/repos/OpenMANET/openmanetd/contributors)
- [Repository security advisories](https://github.com/OpenMANET/openmanetd/security/advisories)
