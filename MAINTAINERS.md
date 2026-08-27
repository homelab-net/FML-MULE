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

Two controlling documents say the same thing in their own terms:

- **CONOPS section 76** requires, before fielding, at least one **additional
  qualified builder or maintainer**. It is section 79 criterion 33, verified by
  inspection at Stage 13, and it is currently unmet.
- **CONOPS section 7.6** requires a standing Communications and Identity
  Management function responsible for onboarding, identity issuance, revocation,
  mission credentials, node identities, re-keying and audit records, and states
  it **shall exist and be staffed before fielding**.
- **SAD section 30.2** makes assigning a named individual and a target date to
  every open TBR an **SRR exit action**. All sixteen read `TBD-SRR`.
- **SAD section 31** carries "one individual owns too many TBRs/release
  functions" as an OPEN risk, to be reviewed when names are assigned.

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
| TAK and service plane | VACANT | VACANT | - |
| Power, thermal and mechanical | VACANT | VACANT | - |

### Relationship to the SAD function owners

SAD v0.31 section 30.2 assigns a **function owner** to each of the sixteen open
trades. Those functions map onto the roles above:

| SAD function owner | Role here |
| --- | --- |
| Power/Mechanical | Power, thermal and mechanical |
| Platform, Linux/Platform | Build and image pipeline |
| Network + RF, RF/Spectrum | Radio and RF |
| Security, Security/Identity | Security and identity |
| Systems + Builder | Hardware |
| TAK, SRE | TAK and service plane |
| CM | Documentation, Release |

The last two rows of the trade register's owner column matter most: SAD section
30.2 requires a **named individual** per trade, and every trade currently reads
`TBD-SRR`.

### What each role covers

- **Build and image pipeline.** `os/image/`, `os/ansible/`, `os/config/`,
  `tools/`, CI. Owns reproducibility, and owns the answer to "can someone else
  build this". Also owns the **hardware-in-the-loop release bench** required by
  SAD section 20.4, without which `TBR-LINUX-01` cannot close.
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
  compatibility-set rule (`FML-ADR-040`), and the deployment freeze.
- **TAK and service plane.** `services/`, `TBR-TAK-01`, `TBR-HA-01`,
  `TBR-ID-01`, and the three approved MULE-original components. Owns the
  original-software count as a controlled metric.
- **Power, thermal and mechanical.** `TBR-PWR-01`, `TBR-THERM-01`,
  `TBR-CARRIER-01`, the battery configuration-item family, and the enclosure.
  Owns the three highest-priority trades in the register.

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
