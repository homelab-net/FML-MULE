# Changelog

Notable changes to this repository. The format follows Keep a Changelog loosely
and the versioning scheme in `os/release/README.md`.

Two things are recorded here that a changelog does not usually carry, because
this program needs them visible:

- **Cold start drills**, including drills that were **skipped**. A silently
  skipped drill is indistinguishable from one that was never scheduled. See
  `docs/verification/README.md`.
- **Deployment freeze exceptions**. A promotion during a freeze is recorded with
  who authorised it, by name. See `os/release/README.md`.

## Unreleased

### The rest of the node's decisions follow, and the repository explains itself

`test/flatsat/node.py` still held four decisions after the time module moved:
what to tell the operator, whether a device may join, what services exist and
what they are called, and which radios matter. All four are now in `mule/`, and
`node.py` does assembly and nothing else. It reads the fakes, hands plain values
to the decision modules, and reports what came back.

The package is organised so that **one file answers one question**:

| File | The question it answers |
| --- | --- |
| `bearers.py` | Which radios can a node have, and which does it need? |
| `timekeeping.py` | Can the clock be trusted? |
| `admission.py` | May this device join the network? |
| `services.py` | What does this node offer, and by what name? |
| `status.py` | What do we tell the operator? |

The decision functions take plain values rather than radios and sensors, so they
are readable and testable without any hardware abstraction in the way. Coverage
of `mule/` is 100% and all 26 mutations are caught, without a single new test:
the existing scenarios already exercised this logic, they just could not reach
it in a form worth reading.

`Bearer` moved with them. It names the node's radio functions per
`FML-ADR-045`, which is decided, and production code cannot import from the test
tree. The Protocols in `test/flatsat/interfaces.py` still stay, for the reason
already recorded there.

**The refactor was caught by its own tooling.** Twelve mutations stopped
applying when the code moved, and `tools/mutation-check.py` reported them as
`NOT-APPLIED` rather than quietly scoring them as caught. That is the check
working: a mutation that cannot be applied is not evidence of anything.

#### Structure and simplicity, in `AGENTS.md`

A new section, because a reader who does not write code should be able to
navigate this repository:

- Every directory carries a `README.md` in plain language, or is named in its
  parent's README where a file of its own would be noise. **Check 12 in
  `tools/validate-docs.sh` enforces it**, across 98 directories.
- Where code goes is decided by **when it runs**: `mule/` is what the node
  decides in the field, `tools/` is what is decided about the node beforehand on
  a builder's machine, `os/` is the image pipeline, `test/` is fakes and
  scenarios and never a decision the node makes.
- Prefer the simplest thing that works. No layer, wrapper or indirection before
  a second caller needs it; no module for work that is anticipated rather than
  done. A clever line that costs a reader ten minutes is a defect in a
  repository maintained by volunteers in their spare time.

Writing that rule surfaced three directories it was not true of: the Ansible
role's `defaults/`, `handlers/` and `meta/`, whose names Ansible fixes and which
would be noise to document individually. The role README now explains the
layout, which is the second form the rule allows.

#### Added

- `mule/bearers.py`, `mule/admission.py`, `mule/services.py`, `mule/status.py`.
- `mule/README.md` rewritten as a plain-language guide: one table of questions,
  the run-time versus build-time split, and what does not belong there.
- Check 12 in `tools/validate-docs.sh`, and a layout section in
  `os/ansible/roles/common/README.md`.
- Mutation `M26`: a service name that drops the deployment's local domain.

### The credibility decision moves into production code

`FML-ADR-051`: node-resident Python that **makes a decision** lives in the new
top-level `mule/` package, and is held to production lint, docstring and typing
standards. Fakes, fixtures, scenarios and flat-sat composition stay under
`test/`.

`mule/timekeeping.py` is the first and only occupant. Splitting the time
credibility decision out of `FakeClock` fixed the test; it left the production
half parked under `test/flatsat/` with a note promising it would move when a
production package existed. That note was a promise nobody was obliged to keep,
and the same review that prompted it found two other stale claims.

The package is bounded rather than open. Nothing enters it until the flat-sat
exercises it end to end - it is a home for demonstrated logic, not a staging
area for intended logic - and it acquires no daemon, no entry point, and none of
the four placeholder components. `FML-ADR-051` records that an accumulation of
unexercised modules is the signal the decision was wrong, and names the fallback.

**The interface Protocols deliberately did not move.** `RadioState`,
`PowerState` and `ThermalState` overlap the radio abstraction that
`docs/interfaces/README.md` records as blocked on `TBR-LINUX-01`, `TBR-RF-01`
and `TBR-RF-03`. Promoting them would be defining a blocked interface by
relocating a file. `timekeeping.py` moved because the decision it makes,
`FML-ADR-042`, is decided; those describe boundaries that are not.

Moving the module closes no trade and baselines no number. `TimePolicy` still
has no defaults: the caller supplies the image build time, the forward horizon
and the skew tolerance, and every one of them belongs to `TBR-TIME-01`.

#### Added

- `mule/`, with `__init__.py`, `README.md` and `timekeeping.py`.
- `FML-ADR-051`, and its row in the ADR register.
- `pythonpath = ["."]` in `pyproject.toml`, so `mule` imports identically under
  a bare `pytest` and under `python -m pytest`. Verified against an interpreter
  with the repository root off `sys.path`.

#### Changed

- The `test/**` ruff relaxations no longer reach the decision logic, which was
  the concrete cost of leaving it in the test tree.
- `tools/mutation-check.py` mutates `mule/timekeeping.py` at its new path. Six
  of the twenty-five mutations target the credibility decision; all 25 are
  still caught.
- `test/flatsat/interfaces.py` carries a corrected location note explaining why
  it stayed, rather than one promising a move that will not happen.
- `AGENTS.md` gains the placement rule.

### Red team of the flat-sat, and the fixes it forced

The flat-sat was audited adversarially before anything was baselined against it,
by mutation testing rather than inspection: sixteen deliberate breaks were
applied to the node one at a time to see which ones the suite noticed.

**Six survived.** Every one had the same shape - hardcode a healthy answer and
nothing objects - because every scenario built a healthy node. Line coverage was
96% at the time, which is the finding worth remembering: coverage measures that
lines ran, not that anything checked them.

Three defects behind it were worse than the score:

- **The flat-sat claimed more than it did.** Its README said it verified the
  CONOPS section 82 end user experience. That flow runs power on, connect,
  authenticate, authorized services appear, operate; the node had no
  authentication, no authorization and no request path, and `admit()` accepted
  any string including an empty one. The claim is now replaced by a table naming
  each uncovered step and the trade blocking it.
- **`FML-ADR-042` was not tested.** The fake returned `CREDIBLE` or `DEGRADED`
  directly, so the fail-closed tests asserted that a fixture agreed with itself.
  No code decided anything.
- **A regulatory check could not fire.** `validate()` compared a resolved EIRP
  against the region profile field it had just been copied from. It read as a
  transmit-power control and was unreachable code.

#### Added

- `test/flatsat/timekeeping.py`: the time credibility **decision**, as
  production code. The platform supplies raw readings, `assess` judges them, and
  a fake can stimulate the decision but no longer stands in for it. Eight rules,
  each with its own operator-readable reason, including the one SAD section
  24.5.1 asks for: a retained time earlier than the running image's build cannot
  be believed, however plausible it looks.
- `tools/mutation-check.py` and `test/flatsat/mutations.yml`: 25 mutations, all
  caught, run in CI. The mutations are data so they can be reviewed as the
  specification of what the suite must detect.
- `test/flatsat/scenarios/test_degraded_states.py` and
  `test_time_fail_closed.py`: the unhealthy half the suite never had.
- `test/flatsat/test_integrity.py`: asserts the flat-sat loads the real
  `tools/gen-config.py` rather than a copy, which rule 1 previously left to an
  import statement and good intentions.
- Three region fixtures for validation branches that had no test at all, and an
  eleventh check in `tools/validate-docs.sh`: every fake must be named in
  `test/flatsat/README.md`, which was a rule nothing enforced.

#### Changed

- **Services come from the mission package.** The node previously served a
  hardcoded `portal.field`; it now serves what a package enables, under the
  domain that package names, and a package enabling none yields none.
- `FakeRadio` raises `ImpossibleHardwareState` for a bearer linked without being
  present. A fake free to describe hardware that cannot exist voids the
  flat-sat's only claim.
- A node missing a required bearer reports `FAULT`, not `GREEN`. It previously
  reported a node with no radios at all as healthy and operational.
- `network_degraded` is derived from which inter-node bearers enumerated rather
  than from HaLow by name, so the access-point-only v0.0.1 configuration is no
  longer reported as permanently degraded.
- The EIRP check now verifies the ceiling is a number the node could enforce
  against, and says plainly why effective-EIRP enforcement is not possible until
  a radio and antenna are selected.
- `RadioState.peer_count` and `PowerState.on_external_power` removed: nothing
  consumed them. Interfaces carry what the node reads and grow when a consumer
  exists.
- `AGENTS.md`: "Region is a parameter, not a constant" generalized to values
  coming from data rather than literals, with the test-specific corollary that a
  test asserting against a literal the code under test also hardcodes proves
  only that the two literals match.

### The flat-sat, and a vocabulary for what testing means here

All testing in this repository is hypothetical until someone brings hardware to
the loop. That was always true; it was not written down, and an unwritten
caveat erodes. It is now stated in `AGENTS.md` as a statement about what the
evidence supports rather than as permission to write untested code, with a
three-tier vocabulary: `UNVERIFIED`, `SIMULATED`, `HARDWARE-VERIFIED`. Nothing
in the repository carries the third.

`test/flatsat/` is the software equivalent of a spacecraft flat-sat: the real
node logic, composed and run end to end, with radio, power, thermal and time
state replaced by fakes behind narrow interfaces. Its purpose is to verify the
**end user experience** in CONOPS section 82, so that what is developed matches
how it will be used and the end-to-end flow is free of logic bugs before
hardware is scarce and expensive.

Its first scenario targets the same flow as the `ROADMAP.md` `v0.0.1`
acceptance criterion, because they are the same flow.

Three rules keep it honest, and they are in `AGENTS.md` rather than only in the
directory: it runs the real artifacts and not parallel copies; every fake is
named in `test/flatsat/README.md`; and a passing scenario yields `SIMULATED`,
never more. The four placeholder services stay unimplemented — the flat-sat
exercises their interfaces with a named stand-in, which is what a flat-sat is
for.

#### Added

- `tools/gen-config.py`, the first code intended for prototype hardware. It
  resolves node configuration from a region profile and a mission package, and
  its most important behaviour today is **refusing to invent a value that is
  still `TBD`**, naming the trade that will supply it. Distinct exit codes
  separate "not decided yet" (3) from "not permitted" (4).
- `test/flatsat/`: `interfaces.py`, `fakes.py`, `node.py`, `scenarios/`, and a
  `README.md` naming every fake, what each does and does not simulate, and the
  trade that replaces it.
- `test/fixtures/regions/xx-testfixture/`, three synthetic region profiles.
  They sit outside `regions/` deliberately, so an invented number can never be
  mistaken for a deployable regulatory profile.
- `test/unit/test_gen_config.py`, including a tripwire asserting that **every**
  committed region profile is still unresolvable.

#### Changed

- `AGENTS.md`: the evidence-tier table, a `## The flat-sat` section, and two
  further entries under "Never do this".
- `test/README.md`, `CONTRIBUTING.md`, `docs/glossary.md` and
  `docs/verification/README.md` carry the same vocabulary.
- `docs/verification/FML-MULE-ITEP-v0.1.md` gained rig **R0**, the flat-sat.
  It is the only rig that needs no hardware and the only one that can produce
  no `HARDWARE-VERIFIED` result.
- `pyproject.toml`: `test/flatsat` added to `testpaths`.

### Integrated Test and Evaluation Plan

`docs/verification/FML-MULE-ITEP-v0.1.md` completes the third and last of the
three artifacts SAD section 33.1 says should proceed immediately. It converts
the SAD section 30.3 dependency graph and the CONOPS section 78 stages into
eleven campaigns, each with a rig, instrumentation, a procurement gate, an
evidence path and a function owner.

It invents no dates, per SAD section 30.2, and no stage pass criteria, which
need `TBR-HW-01`. Its authoring judgement calls are listed in its own section
0.4 rather than left implicit.

`tools/validate-docs.sh` gained a tenth check: **every open trade must appear in
the ITEP.** A trade with no plan to close it is a trade that will not close, and
the plan must not fall silently behind the register.

Four gaps the plan surfaced, recorded rather than resolved: the HIL bench
conflicts with the deployable fleet once one exists; `TBR-RF-03` feeds
`TBR-PWR-01` while being lower priority; four instrumentation items the
prototype BOM does not buy; and stage definitions remain out of scope for a plan
that closes trades rather than qualifying a design.

### Controlling documents added

**FML/MULE CONOPS v1.01 BASELINE** and **FML/MULE SAD v0.31 DRAFT** are now in
the repository, transcribed verbatim, replacing the placeholders that stated the
controlling documents would be added. A prototype and test BOM was added
alongside them.

The registers were reconciled against those documents. Where the initial
scaffold had invented content, it was replaced.

#### Added

- `docs/conops/FML-MULE-CONOPS-v1.01.txt`, plain text as issued.
- `docs/architecture/FML-MULE-SAD-v0.31.md`, Markdown as issued.
- 21 further ADRs, bringing the register to the **30 controlling decisions** in
  SAD section 0.8: `FML-ADR-025` to `028`, `030` to `039`, `043`, `044`, and
  `046` to `050`.
- `TBR-ID-01`, bringing the trade register to the **16 trades** in SAD section
  30.2, each with its priority, function owner and dependency edges.
- The **13 CONOPS section 78 qualification stages** under `test/stages/`.
- `docs/verification/requirements.md`, the **33 CONOPS section 79 success
  criteria** as structured requirements with their section 85 stage mapping.
  `tools/gen-traceability.sh` now produces a real matrix.
- `docs/change-requests/`, with **PBCR-01**, the parent-baseline change from
  NOMAD-only TAK allocation to the controlled Field Service Plane.
- `hardware/prototype/`, the prototype and test BOM as reviewable CSV with its
  gates, cost model and assumptions.
- `os/config/chrony.conf.template`, and the `10.41.0.0/16` field prefix and
  Debian 13.6 baseline recorded where they belong.
- Two maintainer roles the SAD function owners imply: TAK and service plane, and
  power, thermal and mechanical.

#### Changed, and worth knowing about

- **The critical-path marking was wrong and is corrected.** The scaffold marked
  `TBR-LINUX-01` and `TBR-TAK-01`. The SAD body marks **`TBR-PWR-01`,
  `TBR-COMP-01`, `TBR-THERM-01` and `TBR-TAK-01`** as `CRITICAL`, and places
  `TBR-LINUX-01` eighth by priority. Only `TBR-TAK-01` survives from the
  scaffold's list. The correction is stated in `docs/trades/README.md` rather
  than made silently.
- **`docs/NON-GOALS.md` now transcribes CONOPS section 81**, and records the
  correct promotion bar: a section 86 change request with a minor version
  increment and stakeholder re-approval, **not** an ADR.
- **`gen-status.sh` reported zero unowned trades, which was wrong.** Owners are
  `TBD-SRR`, the SAD's own marker, and the check matched only `TBD`. It now
  counts both, and reports 16 of 16 unowned.
- The four placeholder services now carry their real ADRs. Three are
  **approved** original software; all four remain unimplementable. Approval is
  not permission to start.
- Two `bats` tests hardcoded the next ADR and trade identifier. They now derive
  it, so the register can grow without breaking them for the wrong reason.

#### Not changed

No `[SHALL]`, no section 79 criterion, no section 78 stage and no section 81
exclusion was altered. Those require a CONOPS change request under section 86.

#### Outstanding

**SAD section 35.4 requires a second reviewer** to confirm each `PRESENT` row
against the SAD text and to confirm quoted CONOPS text against the controlled
v1.01 source, recording reviewer and date. **That review has not been
performed.** The transcription passes the documents' own count audits — 145
`[SHALL]` markers, 30 decisions, 140 traced clauses, 16 trades, 11 sources — but
a count is not a reading.

## Initial scaffold

Initial repository scaffold. Structure, conventions, and the design record.
**No functional software, no hardware selection, and no measurement of any
kind.**

### Added

#### Governance and conventions

- `AGENTS.md`, with `CLAUDE.md` symlinked to it: the operating rules any
  contributor or agent tool reads first. Hard constraints, the two-layer kernel
  and userland split, the hardware abstraction rule, and a "never do this" list.
- `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `MAINTAINERS.md`. Every maintainer
  role is recorded as `VACANT`, which is the program's largest current risk.
- Apache 2.0 for code (`LICENSE`), CC BY 4.0 for documentation and hardware
  artifacts (`LICENSE-DOCS`).
- `.gitattributes` with Git LFS tracking for CAD, mechanical and image formats,
  landed before any binary. `.editorconfig`, `.gitignore` covering key and
  credential patterns.

#### Safety, regulation, and security

- `SAFETY.md`: lithium cell sourcing, protection, charging, quarantine, storage,
  transport and disposal, and the sealed-enclosure thermal problem.
- `REGULATORY.md`: the sub-GHz band is region-specific and unavailable in the EU
  and UK; modular certification is voided by antenna substitution; amateur
  integration is disabled by default; no public-safety frequency is authorised
  by appearing in a document.
- `SECURITY.md` with the publication rule, and `THREAT_MODEL.md` recording the
  device's detectable emissions signature, the visibility of peer traffic to
  every authenticated participant, and physical capture as an expected
  condition.

#### Design record

- The `FML-ADR-###` decision register: identifier rules, status vocabulary,
  template, and nine seed decisions (021, 022, 023, 024, 029, 040, 041, 042,
  045) transcribed from the drafted architecture description.
- The `TBR-<AREA>-##` trade register: fifteen open trades, the dependency graph
  feeding hardware selection, and `TBR-LINUX-01` and `TBR-TAK-01` marked as the
  critical path. `TBR-TAK-01` requires no hardware.
- `docs/evidence/`, one directory per trade, each carrying its rules before any
  evidence exists.
- `docs/forks/` fork ledger with an upstream-first policy. No patch is carried.
- `docs/NON-GOALS.md`, an empty `docs/parking-lot.md`, `docs/glossary.md`,
  `docs/verification/` including the quarterly cold start drill, and
  placeholders for the CONOPS and architecture controlling documents, which have
  not been transcribed.

#### Structure

- `regions/` with `us-915` seeded (every value `TBD`) and a `_template`. Region
  is an input to configuration generation, never a constant.
- `hardware/` structured to hold more than one qualified block at once, with a
  block template, `block-a` as a named placeholder, the lifecycle and
  obsolescence register, and `BUILD-ACCEPTANCE.md`.
- `os/`: the two-layer split, `PINS.md` for the compatibility set, an empty
  patch directory, the image pipeline definition, the promotion gate, the
  deployment freeze rule, `SBOM.md`, commented configuration templates carrying
  no radio parameters, and a minimal Ansible skeleton.
- `services/`: the rootless Podman and Quadlet execution model, the
  digest-never-tag rule, logging conventions, and four placeholder components
  that must not be implemented.
- `mission/`: package schema with valid and deliberately invalid examples, all
  identities obviously fake, and the standard, exercise and EMCON profiles.
- `test/`: unit tests, fixtures, stages, results, and a README stating plainly
  that CI has no radios.

#### Tooling

- `tools/validate-docs.sh`, `tools/new-adr.sh`, `tools/new-trade.sh`,
  `tools/gen-status.sh`, `tools/gen-traceability.sh`,
  `tools/validate-mission.py`, `tools/lint.sh`.
- `STATUS.md`, generated and never hand-edited, with a CI check that fails when
  the committed copy is stale.
- Configuration for `shellcheck`, `shfmt`, `ruff`, `yamllint`, `ansible-lint`,
  `markdownlint`, `gitleaks`, `pre-commit`, and `renovate`. Each adjustment to a
  default rule carries a recorded reason.
- One CI workflow running the linters, the document checks, and the unit tests.
  **No build or test workflow**, because there is nothing to build.
- `ROADMAP.md` with a single `v0.0.1` milestone: one node, one service,
  reachable from a phone, built by following the repository alone.

### Not added, deliberately

- Any application daemon. The status aggregator, mission trust, service
  controller and gateways hold a README and nothing else.
- Any specification, measurement, or component selection. Unknown values read
  `TBD` with the trade that will decide them.
- Any claim that anything is tested. Unknown status reads `UNVERIFIED`.
- Any badge.

### Cold start drills

**None run.** The first is due once `README.md` is stable enough to test, and at
this stage its scope is the four-question version in
`docs/verification/README.md`: clone, read, and answer in writing what this
program is, what stage it is at, what is unknown, and what you could help with.

### Deployment freeze exceptions

**None.** No promotion has occurred, because no image has been built.
