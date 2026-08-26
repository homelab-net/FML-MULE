# Security policy

## What this system is

MULE is designed for **unclassified volunteer, training, and communications
experimentation use**. It is not built for, evaluated for, or suitable for
classified information, law-enforcement sensitive information, protected health
information, or any context with a regulatory security obligation.

**The system has not undergone independent security assessment.** No penetration
test, no cryptographic review, no supply-chain audit, and no formal design
review by anyone outside the program has taken place. The program is pre-PDR
and most of the security-bearing components are not built. Treat every security
property described in this repository as **UNVERIFIED** design intent.

`THREAT_MODEL.md` states what the design is intended to defend against and,
more importantly, what it is not. Read it before you rely on anything here.

## Reporting a vulnerability

Report privately. Do not open a public issue for a vulnerability.

- **Preferred:** GitHub private vulnerability reporting on this repository
  (Security tab, "Report a vulnerability"). This creates a private advisory
  thread visible only to maintainers.
- **Alternative:** contact the security and identity maintainer listed in
  `MAINTAINERS.md`. Their published contact route is `TBD` until that role is
  filled; see the note in `MAINTAINERS.md`.

Include what you need to make the problem reproducible: affected component and
commit, what you did, what happened, and what you expected. A proof of concept
helps. Do not include real credentials, real member identities, or real
operational captures in the report; describe them instead.

### What to expect

This is a volunteer program with a small number of maintainers and no funded
on-call. Targets, not commitments:

| Stage | Target |
| --- | --- |
| Acknowledgement that the report was received | 5 working days |
| Initial assessment and severity judgement | 15 working days |
| Status update, if unresolved | every 30 days |
| Public disclosure | by agreement, default 90 days after acknowledgement |

If you do not hear back within the acknowledgement window, escalate to any
other maintainer listed in `MAINTAINERS.md`. Silence is a failure of this
process, not a decision.

We will credit you in the advisory unless you ask us not to. There is no bounty
programme and there will not be one.

### Scope

In scope: code, configuration, and design in this repository, including the
image build pipeline, the configuration templates, the identity and trust
material handling, and the service definitions.

Out of scope: vulnerabilities in upstream projects that this program merely
consumes, unless the way this program consumes them creates or worsens the
problem. Report those upstream; tell us as well if a carried patch under
`docs/forks/` is involved.

Also out of scope, because they are known and documented rather than
undiscovered: the emissions signature of a multi-bearer device, the visibility
of peer traffic to authenticated participants on a shared operational domain,
and the consequences of physical capture. These are stated conditions of the
design in `THREAT_MODEL.md`, not defects. If you can show one is worse than the
threat model claims, that is very much in scope.

## Publication rule

This applies to every contributor, every commit, and every issue or pull
request comment.

**No real mission configuration, deployment location, member identity,
callsign, credential, key, certificate, or operational capture is ever
committed to this repository.** Not in code, not in documentation, not in an
example, not in a test fixture, not in a screenshot, not in a log excerpt
pasted into an issue.

A public repository maintained by the organisation that operates the system is
itself an exposure surface. An adversary reading this repository learns the
design, which is intended. They should not also learn who participates, where
they operate, when they exercise, or what identifiers their equipment carries.

Specifically:

- `mission/examples/` contains **obviously fake identities only**, and every
  example file says so in a header comment.
- `test/fixtures/` may contain radio and system state captured from real
  hardware. Scrub location, identity, and key material before committing, and
  record what was scrubbed.
- Logs pasted into issues get the same treatment. Redact before you paste.
- `.gitignore` covers `*.key`, `*.pem`, `*.p12`, `*.pfx`, `*.jks`, `.env`,
  `secrets/`, and `mission/local/`. That is a backstop, not the control. The
  control is you.

Secret scanning runs in CI. A finding blocks the pull request. If a secret
reaches `main`, treat it as compromised and rotate it; removing the commit does
not undo publication.

## Design intent, all currently unverified

Recorded here so a reader knows what the program is aiming at, and knows that
none of it is yet demonstrated:

- Node identity and mission admission are intended to rest on a program PKI,
  with a mission trust layer above it. The trust boundary is an open trade.
- Trust validation **shall not fail open on invalid time**. A node without a
  credible clock refuses to validate rather than accepting anything; see
  `FML-ADR-042` and `TBR-TIME-01`.
- Protected storage unlock in an unattended field device is unsolved and is an
  open trade, `TBR-SEC-01`. Any implementation that stores the unlock secret
  next to the data it protects is not a solution.
- Services run rootless under Podman by default; see `FML-ADR-029`.
- Container images are referenced by immutable digest, never by tag, so that a
  reviewed artifact is the artifact that runs.
