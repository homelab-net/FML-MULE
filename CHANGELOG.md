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

Initial repository scaffold. Structure, conventions, and the design record.
**No functional software, no hardware selection, and no measurement of any
kind.**

### Added

**Governance and conventions**

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

**Safety, regulation, and security**

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

**Design record**

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

**Structure**

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

**Tooling**

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
