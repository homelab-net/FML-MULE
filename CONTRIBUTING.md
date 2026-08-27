# Contributing

This repository is the design record for a program that is pre-PDR. The most
valuable contributions right now are not features. They are evidence that
closes a trade, a region profile for somewhere the maintainers cannot test, a
datasheet archived before the vendor deletes it, and a report that the
documentation did not work when you followed it.

Read `AGENTS.md` before your first change. It is short, it is the operating
summary of everything below, and it applies to humans as well as to tools.

## Ground rules

1. **Do not invent specifications.** If a value is unknown, write `TBD` and
   reference the trade that will decide it. A plausible-looking number is worse
   than a blank, because a blank gets filled and a number gets quoted.
2. **Do not claim anything is tested.** No badges, no "working", no
   "supported". Three status words exist and they are not interchangeable:
   `UNVERIFIED` (no evidence), `SIMULATED` (exercised end to end on the flat-sat
   against fakes; no claim about physical behaviour), and `HARDWARE-VERIFIED`
   (demonstrated on hardware with recorded evidence; nothing carries it yet).
   See `AGENTS.md` and `test/README.md`.
3. **Every claim about component behaviour cites a datasheet or a
   measurement.** Not a forum post, not a vendor marketing page, not a
   recollection. A citation is a path under `docs/evidence/` or a specific
   document with a version and a date. If you cannot cite it, write it as an
   assumption and mark it `TBD`.
4. **No trade closes on document wording alone.** See below.
5. **Do not implement the placeholder services.** `services/status-aggregator/`,
   `services/mission-trust/`, `services/service-controller/`, and
   `services/gateways/` hold a README and nothing else until their trades
   close.
6. **Nothing real is ever committed.** No key, certificate, credential, real
   callsign, real member identity, real deployment location, or captured
   operational traffic. See the publication rule in `SECURITY.md`. This is the
   one rule where a mistake cannot be fixed by a follow-up commit.

## Modal verbs

In requirement-bearing documents, these words are load-bearing and are used
deliberately:

- **shall** - binding and verifiable. Every `shall` needs an architecture
  allocation and a validating test stage. A `shall` with neither is a defect
  and `tools/gen-traceability.sh` fails the build for it.
- **should** - preferred. Waiverable, with the rationale recorded in the
  document that waives it.
- **may** - permitted. Creates no obligation on anyone.

Do not use `will`, `must`, `needs to`, or `has to` in a requirement. They read
as binding without being traceable as binding.

## Headings and style

Sentence case for headings. No emoji anywhere, in documents, commit messages,
issues, or code comments. British or American spelling is both fine; be
consistent within a document.

Write for a stranger. Every file in this repository will be read by someone
with no other context.

## Architecture decisions

Every architecture decision gets a stable ID in the `FML-ADR-###` namespace.

- **IDs are permanent and never reused.** Not after a decision is abandoned,
  not after a file is deleted.
- **A changed decision supersedes an earlier one and cites it.** You do not
  edit a `SELECTED` ADR to say something different. You write a new ADR, set
  the old one's status to `SUPERSEDED`, and record `superseded-by` on the old
  and `supersedes` on the new.
- Editing an existing ADR is for correcting typographical errors, adding
  consequences that were always true, and updating status. Not for changing
  the decision.

To propose one:

```sh
tools/new-adr.sh "Short decision title in sentence case"
```

That allocates the next unused ID and writes the file from
`docs/adr/FML-ADR-000-template.md`. Fill in context, decision, consequences,
accepted cost, and fallback. Open a pull request with status `PROPOSED` in the
body and a note of which trades it depends on. The status vocabulary is defined
in `docs/adr/README.md`; read it, because `SELECTED PRINCIPLE` and
`SELECTED TARGET` mean specific and different things.

An ADR that cites a trade requires that trade to exist.
`tools/validate-docs.sh` enforces this.

## Trades

An open question with engineering consequences is a trade, with an ID in the
`TBR-<AREA>-##` namespace.

```sh
tools/new-trade.sh RF "Short question in sentence case"
```

Every trade records an owner, the question in one sentence, the options under
consideration, the **closure evidence** required, the **closure gate**, and its
dependencies on other trades. Owner `TBD` is acceptable for a trade nobody has
picked up; it is not acceptable for a trade on the critical path.

### Closing a trade

**A trade does not close because its document was rewritten more confidently.**
This is the rule that most often gets broken, usually with good intentions,
under schedule pressure, by someone who is probably right.

To close a trade:

1. Produce the evidence its closure gate demands: a measurement with the
   instrument and date recorded, a log, a photograph, an archived vendor
   datasheet, or a demonstrated build.
2. Commit that evidence under `docs/evidence/<TRADE-ID>/`. See the README there
   for naming and for what a measurement record must contain.
3. Write or update the ADR that records the resulting decision, citing the
   evidence path.
4. Set the trade status to closed, citing the ADR and the evidence path.

A closure that cites no path under `docs/evidence/` is not a closure. A closure
whose supporting datasheet has since 404'd is not verifiable, which is why
datasheets are archived into the repository rather than linked.

## Evidence

Vendors delete PDFs and discontinue parts. This program has already had a key
module reach end of life before it could be purchased. Archive the datasheet
when you cite it, not when you need it again.

`docs/evidence/<TRADE-ID>/` holds measurements, logs, photographs, and archived
vendor documentation. Record the instrument, the date, the node, and the
configuration for every measurement. An unlabelled number in a text file is not
evidence.

## Hardware abstraction

Two or three physical nodes will exist for a long time, and you probably have
none. Therefore:

- Every function that reads or controls radio, power, thermal, or time state
  **shall** sit behind a narrow interface with a fake or recorded-fixture
  implementation.
- Service-plane and status code **shall** run and be testable on an ordinary
  laptop against fakes, with no radios present.
- Fixtures captured from real hardware go in `test/fixtures/` with the node
  identifier, capture date, and image build recorded alongside.

A change that can only be exercised by the person holding the hardware can only
be reviewed by that person. This rule is the difference between a project one
person works on and one other makers can contribute to.

`test/flatsat/` is where that rule is cashed in: the real node logic composed
end to end with the hardware layer faked, so a contributor with no node can run
the whole user flow and see it work. If you add a fake, list it in
`test/flatsat/README.md`. If you find yourself adding one to make a scenario
pass, stop and ask whether the scenario was testing anything.

## Regions

The sub-GHz band this program targets is region-specific and is not permitted
in Europe or the UK. Region is an input to configuration generation, never a
constant. Do not hardcode a frequency, channel, bandwidth, or transmit power
anywhere. Copy `regions/_template/` to add a region you can speak to. See
`REGULATORY.md`.

## Code standards

Configuration for all of these lives in the repository and runs in CI. Run them
locally before pushing; `tools/lint.sh` runs everything that is installed.

- **Shell.** POSIX `sh` where possible, `bash` where not. Every script starts
  with `set -eu` and a usage comment. `shellcheck` clean, `shfmt -i 2 -ci`
  formatted. Tests in `bats` under `test/unit/`.
- **Python.** `ruff` for lint and format. Type hints on public functions.
  Minimum version pinned in `pyproject.toml`. Tests in `pytest` under
  `test/unit/`.
- **YAML.** `yamllint` clean. **Ansible.** `ansible-lint` clean, and roles pass
  `--check`.
- **Markdown.** `markdownlint-cli2` clean. Long lines are permitted inside
  tables only.
- **Container images.** Referenced by **immutable digest**, never by tag.
  Anywhere in the repository, including examples and documentation.
- **Logging and errors.** Structured logging to the journal. No credential or
  location data in logs by default. Log level configurable per service. Any
  function that can fail returns an explicit error rather than exiting the
  process.

If a linter cannot pass on something, adjust the rule deliberately in its
config with a comment explaining why. Do not disable a linter wholesale, and do
not add a blanket ignore file.

## Diagrams

Diagram sources are committed, not only exports. Prefer Mermaid or plain SVG
for architecture diagrams so they diff and review. Mechanical drawings commit
both the native source and a rendered PDF or PNG. Check `.gitattributes` before
adding a binary format; LFS tracking must exist before the file lands.

## Commits and branches

**Conventional Commits**, with an optional trailer referencing the decision or
trade:

```text
feat: add nftables template for the mesh interface

Refs: FML-ADR-024 | TBR-NET-01
Signed-off-by: Your Name <you@example.org>
```

Types: `feat`, `fix`, `docs`, `build`, `chore`, `test`.

- **Trunk-based.** Short-lived branches into `main`. `main` is protected and
  requires one review.
- **Sign-off is required.** Every commit carries a `Signed-off-by` line
  asserting the Developer Certificate of Origin, version 1.1
  (<https://developercertificate.org/>). `git commit -s` adds it. By signing off
  you certify you have the right to submit the work under this repository's
  licences.
- **Licensing.** Code is Apache 2.0 (`LICENSE`); documentation and hardware
  artifacts are CC BY 4.0 (`LICENSE-DOCS`). The split is recorded as an ADR; if
  you think it should change, that is an ADR, not a pull request that edits the
  licence files.
- **Tags.** `v<MAJOR>.<MINOR>.<PATCH>` for repository releases. Image artifacts
  carry a build date and a content hash; see `os/release/README.md`.

## Pull requests

The template asks which ADR or trade your change affects. Answer it. A change
that affects neither is either trivial or premature, and saying which is part
of the review.

Before you open one:

- `tools/validate-docs.sh` passes.
- `tools/lint.sh` passes.
- If you touched ADR or trade frontmatter, you regenerated `STATUS.md` with
  `tools/gen-status.sh` and committed the result. CI fails if the committed
  file differs from freshly generated output. Never hand-edit it.
- No new mutable image tag, no invented number, no secret.

## Generated files

`STATUS.md` and the traceability matrix are generated. Never edit them by hand.
Change the source frontmatter and regenerate.

## Dependency updates

Automated update proposals are opened but **never auto-merged**. Promotion of a
dependency is a decision, because kernel, driver, firmware, and userspace
promote as one tested compatibility set (`FML-ADR-040`). A bot cannot make that
decision, and a green CI run is not evidence that the set still works.

## If something is unclear

Say so in an issue. A point of confusion in the documentation is a defect in
the documentation, and it is the defect class this program is most likely to
have. The cold start drill in `docs/verification/` exists to generate exactly
these reports; you do not need to wait for the drill to file one.
