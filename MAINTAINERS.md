# Maintainers

Succession in a volunteer program fails quietly. One person holds the build
knowledge, becomes unavailable, and the program stops without anyone deciding
that it should. This file exists to make that failure visible before it
happens, not to describe an organisation that already works.

**Current state: every role below is unfilled.** Everything in this repository
was produced by the program originator, and until names are recorded here, the
program has a single point of human failure in every role simultaneously. That
is the most significant risk this program carries, and it is not a technical
one.

## The 90-day rule

**No role may sit with a single name, or with no name, for more than 90 days
without being raised as a program risk.** Raising it means an issue against the
program, discussed and recorded, not a private worry. A role with a primary and
no alternate is one unavailability away from being unowned.

`tools/gen-status.sh` reads this file and reports vacant roles in `STATUS.md`,
so the gap appears on the front page of the program's status rather than in a
file nobody opens.

## Roles

Each role owns the decisions in its area, reviews changes touching it, and is
the escalation point when a trade in that area stalls. `VACANT` means nobody
holds it. Do not leave a cell blank; blank reads as an oversight, `VACANT`
reads as a fact.

| Role | Primary | Alternate | Held since |
| --- | --- | --- | --- |
| Build and image pipeline | VACANT | VACANT | - |
| Radio and RF | VACANT | VACANT | - |
| Security and identity | VACANT | VACANT | - |
| Hardware | VACANT | VACANT | - |
| Documentation | VACANT | VACANT | - |
| Release | VACANT | VACANT | - |

### What each role covers

- **Build and image pipeline.** `os/image/`, `os/ansible/`, `os/config/`,
  `tools/`, CI. Owns reproducibility, and owns the answer to "can someone else
  build this".
- **Radio and RF.** `regions/`, `hardware/blocks/*/rf/`, the bearer trades
  (`TBR-RF-01`, `TBR-RF-02`, `TBR-RF-03`), coexistence, and the kernel-side
  driver question shared with build (`TBR-LINUX-01`).
- **Security and identity.** `services/identity/`, `THREAT_MODEL.md`,
  `SECURITY.md`, the PKI and mission trust design, `TBR-SEC-01`, `TBR-TIME-01`.
  Receives vulnerability reports.
- **Hardware.** `hardware/`, the block qualification structure, the lifecycle
  and obsolescence register, `TBR-HW-01`, `TBR-PWR-01`, `TBR-THERM-01`,
  `TBR-COMP-01`, `TBR-CARRIER-01`.
- **Documentation.** `docs/`, the ADR and trade registers, the glossary, the
  cold start drill, and the honesty of every status claim in the repository.
- **Release.** `os/release/`, the promotion gate, signing, versioning, the
  compatibility-set rule, and the deployment freeze.

## Contact

No contact route is published for any role, because no role is filled. When a
role is taken, record a contact route the holder is willing to have in a public
repository. Do not record a personal address that the holder would not want
scraped.

The security reporting route in `SECURITY.md` depends on this. Until the
security and identity role is filled, GitHub private vulnerability reporting is
the only working path, and it reaches whoever holds repository administration.

## Becoming a maintainer

There is no committee and no process to game. Contribute in an area,
consistently, for long enough that the existing maintainers can see your work.
Then say you are willing to take the role or the alternate slot. In the current
state, where every slot is open, the bar is lower still: sustained contribution
in an area, and a willingness to answer for it.

An alternate is not a junior. An alternate is the person who takes over when the
primary is unreachable, so an alternate who has never exercised the role is not
really an alternate. The **cold start drill** in `docs/verification/` exists
partly to give alternates a scheduled reason to do the primary's work.

## Succession

If a maintainer becomes unavailable:

1. The alternate takes the role and records the change here.
2. The vacated alternate slot is set to `VACANT` and the 90-day clock starts.
3. Any carried patch set owned by that maintainer is reviewed against
   `docs/forks/README.md`, which requires every fork entry to state the
   consequence of its maintainer becoming unavailable. An unowned carried patch
   is dropped or handed over deliberately; it does not simply stay.
4. Credentials and access held by that maintainer are reviewed.

If **all** maintainers become unavailable, this repository is what remains. That
is the argument for the "a stranger can build one" acceptance criterion in
`README.md`: documentation good enough for a stranger is also documentation
good enough for a successor.
