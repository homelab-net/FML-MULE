# Program FERAL MULE

**MULE** is a **Multi-Bearer Utility Link Equipment**: a standardised, portable,
team-level communications and edge-services appliance for volunteer disaster
response, training, and communications experimentation. One node is a box a
volunteer can carry, that gives a team a working local network and the services
that run on it, in a place where the infrastructure is gone or was never there.

A node hosts a network plane and a mission-service plane on a single
general-purpose Linux compute element, with several radio bearers. Wi-Fi HaLow
(IEEE 802.11ah, sub-GHz) provides the range-oriented IP mesh, using 802.11s with
`batman-adv` in BATMAN-V mode. Conventional Wi-Fi provides a high-throughput
link between nodes and, separately, an access point that an operator's phone or
tablet associates with. LoRa carries an independent low-bandwidth plane, whose
value is that it still works when the IP plane does not.

Above the network sits a TAK-compatible situational-awareness service,
browser-based field services, an identity and mission-trust layer, and an
operator status surface. The system is **local-first**: it is required to remain
useful with no internet, no central server, and no parent infrastructure. That
is not a resilience feature bolted on afterwards; it is the condition the whole
design is built for.

## Maturity: is this useful to you today?

**No, not yet. But the design work is public, and that is the point of this
repository.**

The program is **pre-PDR**. The operational concept is **baselined**
(CONOPS v1.01, pending stakeholder signature). The architecture is **drafted**
(SAD v0.31, an SRR package candidate). **Almost nothing is built, and nothing at
all has been measured.**

Both controlling documents are in this repository, transcribed verbatim. That is
the substantive change from the initial scaffold: the design record is no longer
a set of placeholders.

Concretely, as of now:

- **No hardware has been selected.** Not the compute module, not the enclosure,
  not the battery, not the antennas. No bill of material exists.
- **No image has ever been built.** No node has ever been assembled or booted.
- **Nothing has been tested.** Every status claim in this repository reads
  `UNVERIFIED`, because it is.
- **No number in this repository is a measurement.** No endurance figure, no
  range, no throughput, no power budget, no temperature. Where a value is
  unknown it reads `TBD` and cites the trade that will decide it. Any figure you
  encounter elsewhere claiming to be a MULE specification did not come from this
  program.
- **The repository carries no badges**, deliberately. A green CI run here means
  the files parse and the documents are consistent. CI has no radios.

If you came looking for something to build this weekend, this is not that. If
you came to see how a small program tries to do this honestly, or to help decide
something that is still open, read on.

## A stranger can build one

The program's stated goal, and the criterion it judges its own documentation
against:

> **A stranger can clone this repository and build a working node from it,
> without asking anyone.**

Not "the documentation is complete". Not "an experienced maker could figure it
out". A stranger, from the repository alone.

That criterion drives several things that would otherwise look like overhead: a
build guide is not considered complete until someone other than its author has
followed it successfully; the cold start drill runs quarterly and turns every
point of confusion into an issue; and service-plane code must run on an ordinary
laptop against fakes, because contributors will not have hardware.

Every hardware project believes its instructions are complete. None are.

## Start here

Read in this order. Each part assumes the one before it.

1. **[`SAFETY.md`](SAFETY.md)** and **[`REGULATORY.md`](REGULATORY.md)** — read
   these before you buy or build anything. Lithium cells, sealed-enclosure
   thermal limits, and the fact that the sub-GHz band this program targets is
   **not permitted in the EU or the UK**.
2. **[`docs/conops/`](docs/conops/)** — CONOPS v1.01, what the system is for.
   Baselined. Start at its section 1, then sections 5, 9 and 78.
3. **[`docs/architecture/`](docs/architecture/)** — SAD v0.31, how it is
   arranged. Drafted. Start at its section 1, then 2.1 and 0.8.
4. **[`docs/adr/`](docs/adr/)** — the **30 controlling decisions**, each with a
   permanent `FML-ADR-###` identifier, a status, its consequences, and its
   accepted cost.
5. **[`docs/trades/`](docs/trades/)** — the **16 open trades**, each with a
   function owner, a priority and a closure gate.
6. **[`docs/NON-GOALS.md`](docs/NON-GOALS.md)** — what the program deliberately
   does not do, from CONOPS section 81. Read it before proposing anything.
7. **[`STATUS.md`](STATUS.md)** — the generated current view. Never hand-edited.

If you intend to change anything, also read **[`CONTRIBUTING.md`](CONTRIBUTING.md)**
and **[`AGENTS.md`](AGENTS.md)**. `AGENTS.md` is short and is the operating
summary of every rule here.

## The open critical trades

**Sixteen trades are open. Every one of them is unowned.**

Four are marked `CRITICAL` in the SAD, and the SAD's priority ordering puts the
power, compute and thermal characterization first, because those three bound the
hardware selection everything else waits on.

| Pri | Trade | Question | Hardware |
| ---: | --- | --- | --- |
| 1 | `TBR-PWR-01` | Does the one-host, four-radio architecture close endurance with acceptable pack mass? | yes |
| 2 | `TBR-COMP-01` | What CPU and RAM reserve does the full service catalog need on one host? | partly |
| 3 | `TBR-THERM-01` | Can it run across the field thermal envelope without unacceptable throttling? | yes |
| 9 | `TBR-TAK-01` | Which TAK state is mission-critical, and where is it stored? | **no** |

**`TBR-TAK-01` needs no hardware and can proceed today.** It gates the HA
mechanism, the database decision and three of the four placeholder service
components. It is the highest-value work available to a contributor who owns no
node.

`TBR-HW-01`, the hardware block selection, is a **convergence decision** sitting
behind six other trades. Selecting hardware before they close is how a program
ends up requalifying an enclosure it has already had made.

See [`docs/trades/README.md`](docs/trades/README.md) for the full register and
the dependency graph, and [`STATUS.md`](STATUS.md) for the generated view.

## What is in this repository

| Path | Contents |
| --- | --- |
| `docs/` | The design record: CONOPS v1.01, SAD v0.31, 30 decisions, 16 trades, verification, evidence, fork ledger, change requests. |
| `regions/` | Regulatory profiles. Region is an input to configuration, never a constant. |
| `hardware/` | Qualified hardware blocks, lifecycle register, prototype and test BOM. Nothing selected. |
| `os/` | Image build, kernel pins, configuration templates, provisioning, release process. |
| `services/` | Service plane structure. Four components are deliberate placeholders. |
| `mission/` | Mission package schema, examples with fake identities, profiles. |
| `test/` | Unit tests, the flat-sat, fixtures, the 13 qualification stages, results. |
| `tools/` | Validation, identifier allocation, and generation scripts. |

## What is not in this repository

- **A working node.** What exists is the repository's own tooling, the
  configuration generator, and the flat-sat: the node logic composed end to end
  with radio, power, thermal and time state replaced by fakes. Everything it
  demonstrates is `SIMULATED`, which is a real result about software and no
  result at all about RF, power, thermal or timing. Nothing here is
  `HARDWARE-VERIFIED`; see [`test/README.md`](test/README.md).
- **A production bill of material**, a build guide, or a wiring diagram. A
  **prototype and test BOM** exists in `hardware/prototype/`; it answers what
  must be bought to make the architecture decisions, not what a node is.
- **Any measurement**, of anything. The power figures in the prototype BOM's
  reasoning are engineering estimates superseded by `TBR-PWR-01`.
- **Four service components**: the status aggregator, mission trust, service
  controller, and gateways. Three are now **approved** original software, and
  each still holds a README and nothing else, because the trades that define
  their interfaces have not closed. Approval is not permission to start. Adding
  code there is the most likely way to waste weeks of work here.
- **A TAK high-availability mechanism.** Deliberately unselected, with no ADR,
  until `TBR-TAK-01` classifies the state it would protect.
- **Anything real**: no key, certificate, credential, callsign, member identity,
  deployment location, or operational capture ever enters this repository. See
  [`SECURITY.md`](SECURITY.md).

## Getting involved

The most useful contributions right now are not code.

**If you have no hardware** — which is almost everyone:

- **Close `TBR-TAK-01`.** `CRITICAL`, needs no hardware, and is the single
  highest-value piece of work available.
- **Work `TBR-ID-01`**, whether the browser services need a common identity
  provider. Workflow analysis, no hardware.
- **Work `TBR-NET-01`**, the addressing scheme, so that two independently built
  deployments meeting at an incident do not collide.
- **Add a region profile** for somewhere the maintainers cannot test. The EU and
  UK 863-868 MHz profiles are the significant gaps, and without them this
  repository is unusable to a large share of makers.
- **Run the cold start drill**: clone this, read it, and file an issue for every
  point where it did not make sense. That is a real contribution, not a
  courtesy.
- **Add a flat-sat scenario.** `test/flatsat/` runs the real node logic
  against fakes on an ordinary laptop, with no radios present. A scenario that
  describes how you would actually use a node is the most useful code
  contribution available to someone with no hardware.
- **Archive a datasheet** before the vendor deletes it. This program has already
  had a key module reach end of life before it could be purchased.

**If you have hardware**: `TBR-LINUX-01` is waiting, and so is every fixture in
`test/fixtures/`. Capturing recorded radio, power and thermal state is how one
person with a node makes their observations usable by everyone without one.

**If you want a role**: every role in [`MAINTAINERS.md`](MAINTAINERS.md) is
`VACANT`. That is the program's largest current risk, and it is not a technical
one.

Start with [`CONTRIBUTING.md`](CONTRIBUTING.md) and
[`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).

## Safety and regulation

**Read [`SAFETY.md`](SAFETY.md) before assembling anything.** This is a
hobbyist and volunteer project, not a certified product. There is no
manufacturer standing behind a device you build from this repository and no
warranty of any kind. Most of the realistic harm from a device like this comes
from its lithium battery, and a sealed enclosure full of transmitting radios is
a thermal problem nobody here has yet measured.

**Read [`REGULATORY.md`](REGULATORY.md) before buying a radio module.** The
902-928 MHz hardware referenced here is for regions where that band is
permitted; it is **not usable in the EU or UK**, which use 863-868 MHz.
Substituting an antenna can void a module's certification, and compliance of the
assembled device is the builder's responsibility. Amateur-radio integration is
disabled by default, and no public-safety frequency is authorised merely because
it appears in a reference document.

**Read [`THREAT_MODEL.md`](THREAT_MODEL.md) before relying on this
operationally.** A multi-bearer device has a detectable radio signature; peer
traffic is visible to every authenticated participant; and physical capture is
an expected condition rather than an edge case. If a participant's safety
depends on their location not being discoverable, this system does not provide
that.

## Licence

Code is licensed under the **Apache License 2.0**; see [`LICENSE`](LICENSE).

Documentation and hardware artifacts are licensed under **CC BY 4.0**; see
[`LICENSE-DOCS`](LICENSE-DOCS). That covers Markdown documents, decision
records, trade studies, diagrams, bills of material, mechanical drawings, and
regional profiles.

Code is anything executed by a machine to produce behaviour: shell, Python,
Ansible, systemd and Quadlet units, and configuration templates consumed by a
build. Everything else is documentation.
