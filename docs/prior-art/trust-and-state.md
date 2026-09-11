# Trust, time, management and state candidates

**Evaluated:** 2026-09-11. **Scope:** chrony 4.9, OpenSSH portable 10.5p1,
Smallstep step-ca v0.30.2 and PostgreSQL 18.6. These are source evaluations;
they do not select package builds, trust policy, management exposure or an HA
mechanism.

## chrony

chrony fits the retained-time and fail-closed decision in `FML-ADR-042`. It can
discipline system time from configured NTP sources and record drift and RTC
tracking state. NTP uses UDP 123 when enabled; the optional local command
channel uses its configured Unix socket or UDP 323 policy. Source addresses,
keys, serving policy and fallback behavior remain mission and image inputs.

The evaluated artifact is chrony 4.9 at commit
`8df4f1263e206585e6c4e61352d042c2dd12916a`, dated 2026-08-27 and licensed
GPL-2.0. It has not been run in the MULE flat-sat. Promotion must verify the
exact package, startup ordering, RTC source, loss-of-source behavior,
permissions, reboot persistence and the status readings documented in
`docs/readings.md`.

## OpenSSH server

OpenSSH provides the standard remote-management protocol already directed into
the future image manifest by the Program Owner. The evaluated portable release
is 10.5p1 at commit `b3f7344209832eea8ece447d871ea748767c444b`, dated
2026-08-11. The source carries BSD, ISC and other permissive notices collected
in `LICENCE`.

The server normally listens on configured TCP endpoints and starts with enough
authority to accept connections and authenticate users before separating
privileged and unprivileged work. Host private keys, authorized-user keys,
revocation material and configuration are durable security state. Password
authentication, listener interfaces, allowed users, forwarding, subsystem
access, EMCON behavior and recovery access are not selected by this intake.

The exact artifact has not been run. Adoption remains constrained by the
manifest's owner direction: key authentication only, no password login, and no
unreviewed exposure on the EUD access network. A configuration decision and
negative access tests are required before image promotion.

## Smallstep step-ca

step-ca fits the local PKI pattern preferred by `FML-ADR-036`, but that ADR is
`PREFERRED`, not a final implementation selection. The evaluated artifact is
v0.30.2 at commit `6e8ec61405239cf3f37b2bbf260a587b7d2e4e31`, released
2026-03-23 under Apache-2.0.

The CA exposes a configured HTTPS API, commonly on TCP 9000 in upstream
examples. Its durable boundary includes configuration, the CA database,
certificate and key material, and any KMS or provisioner credentials. Backup,
restore, renewal, revocation and offline-root handling are therefore part of
the product trust design rather than generic container persistence.

The GitHub repository listed four advisories on 2026-09-11. Their published
fixed ranges place v0.30.2 after the fixes in v0.29.0 and v0.30.0. No MULE
prototype has exercised this release, and reuse remains undecided until the
owner selects the PKI implementation and `GAP-10` verifies its boundaries.

## PostgreSQL

PostgreSQL fits the relational state role whose condition in `FML-ADR-034` was
resolved affirmatively by `FML-ADR-071`. The selected TAK continuity boundary
is not database-only: it is the SQL backend plus OpenTAKServer's `config.yml`,
`ca/` and `uploads/`. This intake does not select replication or shrink that
boundary.

The evaluated artifact is PostgreSQL 18.6 at commit
`724edf9bde9d356724ad384a2e196edc3c9f80f7`, released 2026-08-13 under the
PostgreSQL License. The server uses a local socket and configured TCP listeners,
conventionally TCP 5432. Its data directory, WAL, role and authentication state,
TLS material and configuration are durable. It supports physical and logical
backup mechanisms, but the authoritative MULE backup must also carry the
out-of-SQL durable set.

The PostgreSQL security page records 18.6 as the fix release for 28 disclosed
vulnerabilities. Several entries require configuration adjustment or data
cleanup in addition to installing the release, so version comparison alone is
not sufficient promotion evidence. Existing TBR-TAK-01 work demonstrated TAK
workflows on a different PostgreSQL version; it does not qualify 18.6.

## Shared gaps and exit strategy

No component here is a package pin. The userland compatibility set, encrypted
storage boundary, secret provisioning, least privilege, backup retention,
upgrade and rollback paths, resource measurements and clean-host restore tests
remain necessary. Hardware is needed only for the RTC and final device behavior,
not for the source and flat-sat work that precedes it.

chrony stays behind the time-source interface, OpenSSH behind management policy,
step-ca behind standard certificate protocols, and PostgreSQL behind the
application database interface plus an explicit backup contract. These seams
preserve an exit without changing EUD or mission-data formats.

## Sources

- [Pinned chrony source](https://gitlab.com/chrony/chrony/-/tree/8df4f1263e206585e6c4e61352d042c2dd12916a)
- [Pinned chrony license](https://gitlab.com/chrony/chrony/-/blob/8df4f1263e206585e6c4e61352d042c2dd12916a/COPYING)
- [Pinned OpenSSH source](https://github.com/openssh/openssh-portable/tree/b3f7344209832eea8ece447d871ea748767c444b)
- [Pinned OpenSSH license](https://github.com/openssh/openssh-portable/blob/b3f7344209832eea8ece447d871ea748767c444b/LICENCE)
- [OpenSSH security notices](https://www.openssh.com/security.html)
- [Pinned step-ca overview](https://github.com/smallstep/certificates/blob/6e8ec61405239cf3f37b2bbf260a587b7d2e4e31/README.md)
- [Pinned step-ca license](https://github.com/smallstep/certificates/blob/6e8ec61405239cf3f37b2bbf260a587b7d2e4e31/LICENSE)
- [step-ca advisories](https://github.com/smallstep/certificates/security/advisories)
- [Pinned PostgreSQL source](https://git.postgresql.org/gitweb/?p=postgresql.git;a=tree;h=724edf9bde9d356724ad384a2e196edc3c9f80f7)
- [PostgreSQL 18.6 release notes](https://www.postgresql.org/docs/release/18.6/)
- [PostgreSQL security information](https://www.postgresql.org/support/security/18/)
