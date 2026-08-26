# Architecture decision register

Every architecture decision in this program is recorded here as a numbered
document in the `FML-ADR-###` namespace.

An ADR records a decision that was taken, why, and what it costs. It is not a
design document and it is not a specification. If a reader has to ask "why is
it like that", the answer belongs in an ADR.

## Identifier rules

These are binding. `tools/validate-docs.sh` enforces the mechanical parts.

1. **Identifiers are permanent and never reused.** Not after a decision is
   abandoned, not after a file is deleted, not to close a gap in the sequence.
   A gap in the numbering is information; filling it destroys that information.
2. **Filename is `FML-ADR-###-slug.md`**, three digits, lower-case hyphenated
   slug derived from the title.
3. **The `id` in frontmatter matches the filename.**
4. **A changed decision does not edit the old ADR.** Write a new one, set the
   old one's status to `SUPERSEDED` with `superseded-by`, and set `supersedes`
   on the new one. Both directions are recorded so a reader arriving at either
   file finds the other.
5. **Editing an existing ADR** is for typographical corrections, for
   consequences that were always true and were missed, and for status changes.
   Not for changing the decision.
6. **Every trade an ADR cites must exist** as a file in `docs/trades/`.

Allocate an ID with `tools/new-adr.sh "Title in sentence case"`. It will not
hand out a used number, including numbers used by deleted files, because it
reads the highest ID ever recorded rather than counting files.

The number range is not meaningful and is not reserved by area. The seed set
starts at 021 because the decisions numbered below that were taken during the
pre-repository phase of the program and have not yet been transcribed; their
IDs are reserved and will not be reissued.

## Status vocabulary

The status is not a confidence rating. It says what kind of commitment the
decision is, which determines what it takes to change it. Read this section
before setting a status; the distinctions are the point.

| Status | Meaning |
| --- | --- |
| `PROPOSED` | Written, under review, not yet decided. Carries no weight. |
| `SELECTED` | A decision has been taken. Implementation may depend on it. Changing it requires a superseding ADR. |
| `SELECTED PRINCIPLE` | The property is decided; the mechanism that provides it is not. Implementations must satisfy the principle. A later ADR names the mechanism without superseding this one. |
| `SELECTED TARGET` | A value or objective the design is being driven toward, which has not been demonstrated achievable. May be revised downward with recorded rationale rather than superseded. |
| `SELECTED PLANNING BASELINE` | Adopted so that dependent work can proceed. Expected to be revisited when a named trade closes. Nobody should be surprised if it changes. |
| `PREFERRED` | A leaning, not a decision. Recorded so the reasoning is not lost, and so a contributor knows which way the program is inclined. Nothing may depend on it. |
| `CONDITIONAL` | Decided, but contingent on a stated condition. If the condition fails, the decision reverts and the fallback applies. The condition is written in the Status section. |
| `SUPERSEDED` | Replaced by a later ADR, cited in `superseded-by`. Retained permanently. Never deleted. |
| `RETIRED` | No longer applicable because the thing it decided no longer exists. Not superseded, because nothing replaced it. Retained permanently. |

Two distinctions that matter and are commonly confused:

- `SELECTED PRINCIPLE` versus `SELECTED`. `FML-ADR-041` decides that a bootable
  known-good rollback path exists independently of the active root. It does not
  decide whether that is an A/B slot scheme, a recovery partition, or something
  else. An implementation ADR will decide the mechanism and will **not**
  supersede `FML-ADR-041`, because the principle still holds.
- `SELECTED PLANNING BASELINE` versus `PREFERRED`. A planning baseline is
  something dependent work is allowed to build on, with the understanding that
  it may move. A preference is something nothing may build on.

## Frontmatter

Every ADR begins with YAML frontmatter. `tools/gen-status.sh` and
`tools/validate-docs.sh` read it, so the field names and the flow-sequence
syntax are fixed.

```yaml
---
id: FML-ADR-021
title: Single primary compute element, single Debian-family host
status: SELECTED
date: TBD
supersedes: none
superseded-by: none
trades: [TBR-COMP-01, TBR-HW-01]
verification: TBD
---
```

- `status` is one of the values above, spelled exactly.
- `date` is the date the status was last changed, `YYYY-MM-DD`, or `TBD` where
  the decision predates the register.
- `supersedes` and `superseded-by` are an ADR ID or `none`.
- `trades` is a flow sequence of trade IDs, or `[]`. Every ID listed must
  exist as a file in `docs/trades/`.
- `verification` names the test stage that validates the decision, or `TBD`.

## Required sections

Each of these headings appears in every ADR. `tools/validate-docs.sh` fails a
file that is missing one. An empty section is permitted only with `TBD` and a
reason; a missing section is not.

- **Context** - the situation that forced a decision. What constraint, what
  conflict, what alternative was on the table.
- **Decision** - what was decided, in the active voice, using `shall` where the
  decision is binding.
- **Status** - the status value, and for `CONDITIONAL` the condition, for
  `SELECTED TARGET` what has not been demonstrated, for
  `SELECTED PLANNING BASELINE` the trade that will revisit it.
- **Consequences** - what follows, including what becomes harder. An ADR that
  lists only benefits has not been thought about.
- **Accepted cost** - what the program is knowingly giving up. Distinct from
  consequences: this is the part someone will later argue was a mistake, so
  write it down before they do.
- **Fallback** - what happens if this turns out to be wrong. Sometimes "none,
  this is structural"; say so explicitly rather than leaving it blank.
- **Superseded by** - an ADR ID or `None`.
- **Verification dependency** - the test stage or evidence that would confirm
  the decision holds, or `TBD` with the trade that will define it.

## The seed set

These ADRs were transcribed into the register from the drafted architecture
description. **The architecture document is the source of rationale**; the ADRs
here record the decision, its status, and its consequences, and point at that
document. Where an ADR body reads thin, that is why: the reasoning has not been
transcribed yet, and inventing it here would misrepresent it as the register's
own.

| ID | Title | Status |
| --- | --- | --- |
| `FML-ADR-021` | Single primary compute element, single Debian-family host | `SELECTED` |
| `FML-ADR-022` | Host operating system family | `SELECTED` |
| `FML-ADR-023` | Consume the upstream MANET reference project as configuration knowledge, not as mandatory production firmware | `SELECTED` |
| `FML-ADR-024` | 802.11s plus batman-adv and BATMAN-V as the baseline IP MANET | `SELECTED` |
| `FML-ADR-029` | Rootless Podman and Quadlet as the default application execution model | `SELECTED` |
| `FML-ADR-040` | Kernel, driver, firmware and userspace promote as one tested set | `SELECTED` |
| `FML-ADR-041` | Bootable known-good rollback path independent of the active root | `SELECTED PRINCIPLE` |
| `FML-ADR-042` | Retained local time via battery-backed RTC, trust validation never fails open on invalid time | `SELECTED` |
| `FML-ADR-045` | EUD access point and high-throughput inter-node mesh are separate logical radio functions | `SELECTED PLANNING BASELINE` |

`STATUS.md` at the repository root carries the generated current view. This
table is a reading aid and may lag; the generated one does not.

## Decisions not yet recorded

The licensing split (Apache 2.0 for code, CC BY 4.0 for documentation and
hardware artifacts) is a program decision that has not been written as an ADR.
It should be. It is listed here rather than silently omitted.
