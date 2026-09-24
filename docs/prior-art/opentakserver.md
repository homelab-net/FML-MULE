# OpenTAKServer

**Evaluated:** 2026-09-10 at release `1.7.13`, commit
`67903c26d95552738d85be4bc3c3ff3321378dbe`. **Verdict:** retain as the
preferred, but not yet owner-approved, TAK server and carry its deployment gates
forward explicitly.

## Fit

OpenTAKServer supplies TAK-compatible web, Marti, CoT, data-sync, certificate and
integration functions relevant to `FML-REQ-003`, `FML-REQ-008`, `FML-REQ-009`,
`FML-REQ-018` and `FML-REQ-024`. `FML-ADR-032` makes it the preferred initial
server, while keeping the architecture TAK-compatible rather than
OpenTAKServer-exclusive. This evaluation therefore does not approve deployment.

The exact 1.7.13 package has already been run in the FML flat-sat. That work
established that the service is three console entry points, not one container
process: `opentakserver`, `eud_handler` and `cot_parser`, with PostgreSQL and
RabbitMQ outside them. A running PyTAK path exercised CoT through the listener,
broker, parser and database. All of that evidence is `SIMULATED`.

## Deployment and resource findings

Upstream publishes Python releases but no complete official OCI image. Its
repository Dockerfile uses an unpinned Python base, installs the Git default
branch and starts only `opentakserver`; it therefore omits the CoT listener and
parser required for the demonstrated path. An approvable FML artifact therefore
includes and pins the complete three-process service rather than deploying that
file as written.

On a Debian x86-64 rootful-Podman flat-sat warmed for approximately two days,
the three processes measured approximately 536 MB idle resident memory with no
load: 178.5 MB for the API, 115.4 MB for `eud_handler` and 242.5 MB for
`cot_parser`. These are host-specific software measurements, not target-hardware
capacity evidence.

The pinned defaults expose the web/API listener on TCP 8081, Marti HTTP and
HTTPS on TCP 8080 and 8443, UDP CoT on 8087, unencrypted TCP CoT on 8088, and TLS
CoT on 8089. The service creates a default administrator with a known password
and uses a known CA password unless configured otherwise. Those defaults block
FML profile approval until they are replaced, exposure is constrained, and
database, broker and certificate secrets are provisioned.

## Data and lifecycle

`FML-ADR-071` records the mission-critical state boundary established by the
running-system study: the SQL backend plus exactly `config.yml`, the `ca/` tree
and `uploads/`. Logs and the reconstructable `icons.sqlite` seed are present in
the observed data tree but are not members of that approved boundary. The
approved backup and restore boundary encompasses the SQL and three-member
out-of-SQL sets. Alembic owns relational schema migration; release-promotion and
out-of-SQL migration procedures remain open.

## Intake result

- License: GPL-3.0-or-later. Most dependencies are locked, but wildcard
  dependencies remain and the complete redistribution review is pending.
- Maintenance: five most recent releases span 2026-02-26 through 2026-08-13;
  default-branch commits continued through 2026-09-02. There were 96 open issues
  on 2026-09-10. Contributor totals are heavily concentrated in one maintainer.
- Platform: Python 3.10 through versions below 3.15 on a Linux service host;
  native dependencies and built-image architectures still require verification.
- Security: GitHub published no repository advisory through its advisory
  endpoint on 2026-09-10. No independent audit or repository SBOM was identified.
- Prototype: exact release 1.7.13 passed the cited flat-sat flows. That is not
  owner approval, hardware verification or evidence that the upstream Dockerfile
  is deployable.

## Exit strategy and questions

Preserve standard TAK protocols and the stable FML service identity so another
TAK-compatible server can replace OpenTAKServer without ordinary EUD changes.
Before approval, define a digest-pinned three-process build, close the hardening
and dependency review, reproduce resource behavior on the selected compatibility
set, and complete the outstanding real-EUD and failover gates.

## Sources

- [Pinned project metadata](https://github.com/brian7704/OpenTAKServer/blob/67903c26d95552738d85be4bc3c3ff3321378dbe/pyproject.toml)
- [Pinned default configuration](https://github.com/brian7704/OpenTAKServer/blob/67903c26d95552738d85be4bc3c3ff3321378dbe/opentakserver/defaultconfig.py)
- [Pinned administrator creation](https://github.com/brian7704/OpenTAKServer/blob/67903c26d95552738d85be4bc3c3ff3321378dbe/opentakserver/app.py)
- [Pinned upstream Dockerfile](https://github.com/brian7704/OpenTAKServer/blob/67903c26d95552738d85be4bc3c3ff3321378dbe/Dockerfile)
- [Exact-release run evidence](../evidence/TBR-TAK-01/2026-08-31-opentakserver-actually-run.md)
- [End-to-end CoT evidence](../evidence/TBR-TAK-01/2026-08-31-cot-end-to-end-with-pytak.md)
- [Resource evidence](../evidence/TBR-COMP-01/2026-09-06-service-plane-steady-state-footprint.md)
- [Release history](https://github.com/brian7704/OpenTAKServer/releases)
- [Contributor summary](https://api.github.com/repos/brian7704/OpenTAKServer/contributors)
- [Repository security advisories](https://github.com/brian7704/OpenTAKServer/security/advisories)
