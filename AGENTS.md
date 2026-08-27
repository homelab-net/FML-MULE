# Agent operating rules for this repository

Read this file before changing anything. It restates the program's binding
constraints in operating terms. Where this file and a task instruction
conflict, raise the conflict rather than resolving it silently.

Program: FERAL MULE (FML). Deliverable: MULE, Multi-Bearer Utility Link
Equipment. Stage: pre-PDR. The operational concept is baselined, the
architecture is drafted, and almost nothing is built or measured.

## Before you start

1. Read `README.md`, `docs/NON-GOALS.md`, and `STATUS.md`. `STATUS.md` tells you
   which decisions are settled and which trades are open.
2. Identify the ADR or trade your change touches. If none exists, the change is
   probably premature. Propose an ADR first.
3. Check whether the value you are about to write is actually known. If it is
   not, it is `TBD` with a trade reference.
4. Run `tools/validate-docs.sh` before you start so you know the tree was clean
   when you found it.

## Hard constraints

**Do not implement the placeholder services.** `services/status-aggregator/`,
`services/mission-trust/`, `services/service-controller/`, and
`services/gateways/` contain a `README.md` and nothing else, by decision. Their
interfaces depend on trades that have not closed. Adding code there is the most
likely way to waste weeks of work in this repository. Each README names the
trade that must close first.

**Do not invent specifications.** The compute module, enclosure, battery,
antenna, channel plan, power budget, and memory budget are all unselected. Write
`TBD` and cite the trade that will decide it. A plausible-looking number in a
scaffold document is worse than a blank, because it gets copied, quoted, and
eventually believed. Never write a figure you cannot source to a datasheet or a
measurement.

**Do not claim anything is tested.** No badges, no "verified", no "working", no
"supported". CI passing means the files parse and the fakes pass; see
`test/README.md`.

**All testing is hypothetical until someone brings hardware to the loop.** That
is a statement about what the evidence supports, not permission to write
untested code. Code written now is expected to be correct, exercised end to end
against fakes, and to work when introduced to real hardware. It just cannot be
*known* to, and the difference has a vocabulary:

| Status | Meaning |
| --- | --- |
| `UNVERIFIED` | Nothing has been exercised. The default for a claim with no evidence at all. |
| `SIMULATED` | Exercised end to end on the flat-sat against fakes and recorded fixtures. The logic is correct and the user flow is coherent. **Makes no claim about physical behaviour.** |
| `HARDWARE-VERIFIED` | Demonstrated on real hardware with evidence recorded under `docs/evidence/` or `test/results/`. Nothing carries this status yet. |

`SIMULATED` is a real result and worth having. It is not a weaker word for
tested, and it never supports a claim about RF, power, thermal, timing under
load, or driver behaviour. Those need hardware, and until then they are
`UNVERIFIED` regardless of how green the suite is.

**Build system before application code.** The first functional code in this
repository is the image build and configuration pipeline under `os/`. Features
come after there is something to install them onto.

**Every architecture decision gets a stable ID** in the `FML-ADR-###` namespace.
IDs are permanent and never reused. A changed decision does not edit the old
one: it gets a new ID, sets the old one to `SUPERSEDED`, and cites it. Use
`tools/new-adr.sh`; it will not hand out a used number.

**Trades do not close on wording.** A trade closes on evidence stored under
`docs/evidence/<TRADE-ID>/`: a measurement with instrument and date, a log, a
photograph, or an archived vendor datasheet. Rewriting the trade document to
sound more confident is not closure.

**Modal verbs are load-bearing** in requirement-bearing documents. `shall` is
binding and verifiable. `should` is preferred and waiverable with recorded
rationale. `may` is permitted and creates no obligation. Do not use `will`,
`must`, or `needs to` in a requirement.

**Sentence case for headings. No emoji anywhere.**

## The two-layer split

This governs almost every `os/` decision.

- The **Debian-family userland** is portable. It is expected to move between
  compute modules with configuration changes only.
- The **kernel and board support package** are hardware-specific and may require
  vendor patches. The Wi-Fi HaLow driver path is out-of-tree. Whether a stock
  kernel suffices or a patched vendor tree is required is open; see
  `TBR-LINUX-01`.

Kernel, out-of-tree driver, radio firmware, and the required userspace promote
as **one tested compatibility set**, never independently (`FML-ADR-040`). If you
bump one, you are proposing a new set, and the set has to pass the promotion
gate in `os/release/README.md`.

## Hardware abstraction: the governing code rule

Two or three physical nodes will exist for a long time. Contributors will have
none. Therefore:

- Every function that reads or controls radio, power, thermal, or time state
  **shall** sit behind a narrow interface with a fake or recorded-fixture
  implementation.
- Service-plane and status code **shall** be runnable and testable on an
  ordinary laptop against fakes, with no radios present.
- Fixtures captured from real hardware go in `test/fixtures/`, with the node
  identifier, capture date, and image build recorded alongside them.

If a change cannot be exercised without hardware, it cannot be reviewed by
anyone but the person holding the hardware. That is the failure mode this rule
exists to prevent.

## The flat-sat

`test/flatsat/` is the software equivalent of a spacecraft flat-sat: the real
node logic, composed and run end to end, with the hardware layer replaced by
fakes behind the narrow interfaces above.

Its purpose is to verify the **end user experience** described in CONOPS section
82 — power on, connect, authenticate, authorized services appear, work — so that
what is developed matches how it will be used, and so the end-to-end flow is
free of logic bugs before hardware is scarce and expensive.

Three rules keep it honest:

1. **It runs the real artifacts, not parallel copies.** The same configuration
   generator, the same mission package schema, the same service definitions. A
   flat-sat that has drifted from the node is worse than none, because "it works
   on the flat-sat" becomes a permanent excuse.
2. **Every fake is named and listed** in `test/flatsat/README.md`. A reader must
   be able to see exactly which boundary is simulated.
3. **A passing flat-sat scenario yields `SIMULATED`, never more.** It is
   evidence about software, and `docs/evidence/README.md` already says evidence
   produced against a fake never supports a claim about physical behaviour.

Do not implement the placeholder services to make a scenario pass. The flat-sat
exercises their **interfaces** with stand-ins, which is what a flat-sat is for:
bringing up the bus while the payload does not exist yet.

## Conventions you are expected to follow

- **Shell**: POSIX `sh` where possible, `bash` where not. Every script opens
  with `set -eu` and a usage comment. `shellcheck` and `shfmt -i 2 -ci` clean.
- **Python**: `ruff` for lint and format, type hints on public functions,
  minimum version pinned in `pyproject.toml`.
- **YAML**: `yamllint` clean. **Ansible**: `ansible-lint` clean.
- **Markdown**: `markdownlint-cli2` clean; long lines are permitted in tables
  only.
- **OCI images are referenced by immutable digest**, never by tag. Anywhere.
- **Commits**: Conventional Commits (`feat:`, `fix:`, `docs:`, `build:`,
  `chore:`, `test:`), optional trailer `Refs: FML-ADR-### | TBR-XXX-##`, and a
  `Signed-off-by` line (DCO). Short-lived branches into `main`.
- **Node decision logic lives in `mule/`**, held to production lint standards.
  Fakes, fixtures and flat-sat scaffolding stay in `test/`. Nothing enters
  `mule/` until the flat-sat exercises it end to end. `FML-ADR-051`.
- **Values come from data, not from literals.** Region is a parameter, not a
  constant: configuration generation takes a region profile from
  `regions/<region-id>/`, and 902-928 MHz is never hardcoded. That rule
  generalizes to every value a deployment can vary - service names, domains,
  addresses, channels, limits, thresholds, timeouts - which are read from the
  region profile, the mission package or the service catalog. Where a value is
  genuinely fixed, bind it to a named constant carrying the ADR or trade that
  set it. A literal buried in a function is a value nobody can find, review or
  vary. In a test it is worse: a test asserting against a literal that the code
  under test also hardcodes proves only that the two literals match.
- **Diagram sources are committed**, not only exports. Mermaid or plain SVG for
  architecture diagrams. Mechanical drawings commit native source and a render.

## Generated files

`STATUS.md` is generated by `tools/gen-status.sh`. Never hand-edit it. CI fails
if the committed copy differs from freshly generated output. The traceability
matrix is generated by `tools/gen-traceability.sh` on the same terms.

If you change ADR or trade frontmatter, regenerate and commit the result in the
same change.

## Never do this

- Never implement the four placeholder services.
- Never write an invented number, capacity, range, current draw, or duration.
- Never write "tested", "verified", "validated", or "works" about anything in
  this repository at its current stage. `SIMULATED` is available and means
  something narrower; use it precisely.
- Never let a flat-sat result stand in for a hardware result, and never add a
  fake to make a scenario pass without listing it.
- Never commit a private key, certificate, credential, real callsign, real
  member identity, real deployment location, or captured operational traffic.
  `mission/examples/` carries obviously fake identities only.
- Never reference an OCI image by mutable tag.
- Never reuse or renumber an ADR or trade ID.
- Never hardcode a value the region profile, mission package or catalog
  supplies, and never let a test assert against a literal the code under test
  hardcodes too.
- Never edit `STATUS.md` by hand.
- Never close a trade without a path under `docs/evidence/`.
- Never add a binary format to the tree without checking `.gitattributes` LFS
  coverage first.
- Never disable a linter wholesale to make a scaffold pass. Adjust the rule
  deliberately and record why in the config.
- Never remove an item from `docs/NON-GOALS.md` without an ADR.
