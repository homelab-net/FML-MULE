# Agent operating rules

Read this before changing anything. These are the rules; the reasoning lives in
the documents named at the bottom. Where a rule and a task instruction conflict,
**raise the conflict, do not resolve it silently.**

Program: FERAL MULE (FML). Deliverable: MULE, Multi-Bearer Utility Link
Equipment. Stage: pre-PDR. The concept is baselined, the architecture is
drafted, and almost nothing is built or measured. Most of what looks like a gap
is a decision nobody has earned the right to make yet.

## Start

1. Read `STATUS.md`. It says which decisions are settled and which trades are
   open. Do not guess at either.
2. Name the ADR or trade your change serves. If there is none, the change is
   probably premature: propose an ADR first.
3. Run `tools/lint.sh`. You need to know the tree was clean when you found it.

## Done

A change is not done until all five hold. Say which ones you actually ran.

1. `tools/lint.sh` passes. It runs every linter, the document checks, the
   mission schema, the shell tests and the mutation check. **Read its exit
   code, not its last line of output.**
2. New behaviour has a test that **fails without the change**. A test that
   passes either way is decoration.
3. Any rule you added is enforced by a check, or you have said plainly why it
   cannot be.
4. If you touched ADR or trade frontmatter, `STATUS.md` and the traceability
   matrix are regenerated and committed in the same change.
5. You can name the evidence for every claim you wrote down.

## The five that waste the most work

1. **Implementing the placeholder services.** `services/status-aggregator/`,
   `mission-trust/`, `service-controller/`, `gateways/` hold a README and
   nothing else, by decision. Their interfaces depend on open trades. Each
   README names the trade that must close first. `[review]`

   A pure decision function in `mule/` **may** reason about their subject
   matter, on the four conditions in `FML-ADR-052`. Being in a different
   directory is not one of them, and was the rule this program tried first.
   `[review]`, with the cross-reference obligation `[CI]`.
2. **Inventing a specification.** Compute module, enclosure, battery, antenna,
   channel plan, power budget, memory budget: all unselected. `[review]`
3. **Claiming something is verified.** Nothing here has met hardware. The word
   `HARDWARE-VERIFIED` is machine-checked `[CI]`; every softer claim is on you
   `[review]`, and softer claims are how this has actually gone wrong.
4. **Committing anything real.** No key, certificate, credential, callsign,
   member identity, deployment location, or captured traffic, ever.
   `mission/examples/` carries obviously fake identities only. `[CI]`
5. **Reusing or renumbering an identifier.** `FML-ADR-###` and `TBR-XXX-##` are
   permanent. A changed decision gets a new ID and supersedes the old one; it
   never edits it. Use `tools/new-adr.sh`. `[CI]`

## Before you write

| You are about to write | Do this first |
| --- | --- |
| A number, capacity, range, current draw or duration | Source it to a datasheet or a measurement. If you cannot, write `TBD` and cite the trade that will decide it. |
| A claim about what works | Name the evidence. If the evidence is a fake, the claim is `SIMULATED` and says nothing about physical behaviour. |
| A value a deployment could vary | Read it from the region profile, mission package or service catalog. Never a literal. |
| A value that is genuinely fixed | Bind it to a named constant carrying the ADR or trade that set it. |
| A requirement | `shall` binds and is verifiable. `should` is waiverable with recorded rationale. `may` creates no obligation. Never `will`, `must`, or `needs to`. |
| A test assertion | Assert against data or a named constant, never against a literal the code under test also hardcodes. That proves only that two literals match. |
| A hardware reading interface | Say where the value really comes from on a Debian node, and what the platform returns when it cannot answer. If "nothing" is possible, the type is `T \| None`. Add the row to `docs/readings.md`. `[CI]` |
| A reading's source | Prefer a kernel interface (`sysfs`, `procfs`) to a command. A command is a package in the image, a fork per reading, and output that is not ABI-stable. Where only a command exists, name the package that provides it. `[CI]` |
| A reading that returns a number | Put the unit in the method name. Linux reports the same quantity in millidegrees, tenths and percents depending on the subsystem, and every conversion is a factor-of-a-hundred error that produces a plausible number. `[CI]` |
| Code touching a blocked `services/` component's subject matter | Check it against all four `FML-ADR-052` conditions: pure function, no invented vocabulary, `None` where the blocking trade decides, no interface an open trade governs. Then name the module in that component's README. `[CI]` |
| A test that exercises a multi-step path | Test the single-step case first. A failure in the interesting case is uninterpretable until the boring one passes, and this program spent five runs debugging multi-hop mesh routing when the fault was that no two nodes could exchange a packet at all. |
| A new check | Prove it can fail. Break something on purpose and watch it fire. **Remove every instance of what it looks for**, not one. |
| A heading, or any prose | Sentence case. No emoji. Anywhere. |

## What the evidence supports

All testing is hypothetical until someone brings hardware to the loop. That is
a statement about evidence, not permission to write untested code. Code written
now is expected to be correct, exercised end to end against fakes, and to work
when it meets real hardware. It just cannot be *known* to.

| Status | Meaning |
| --- | --- |
| `UNVERIFIED` | Nothing exercised. The default for a claim with no evidence. |
| `SIMULATED` | Exercised end to end on the flat-sat against fakes and recorded fixtures. The logic is correct and the user flow coherent. **Says nothing about physical behaviour.** |
| `HARDWARE-VERIFIED` | Demonstrated on real hardware, evidence under `docs/evidence/` or `test/results/`. **Nothing carries this.** |

`SIMULATED` is a real result and worth having. It is not a softer word for
tested, and it never supports a claim about RF, power, thermal, timing under
load, or driver behaviour.

Trades close on evidence under `docs/evidence/<TRADE-ID>/` accepted by a named
owner, never on rewriting the trade document to sound more confident.

## Where things go

Decided by **when the code runs**, not by what it is about.

| Directory | What lives there |
| --- | --- |
| `mule/` | Decisions the node makes while running, one module per question. Production standards, none of the `test/` relaxations. `FML-ADR-051`. |
| `tools/` | Decisions made about the node beforehand on a builder's machine, and repository tooling. |
| `os/` | The image build and configuration pipeline. Build system before application code. |
| `test/` | Fakes, fixtures, scenarios, the flat-sat. Never a decision the node makes. |

Nothing enters `mule/` until the flat-sat exercises it end to end. It is a home
for demonstrated logic, not a staging area for intended logic.

**Everything that reads or controls radio, power, thermal or time state shall
sit behind a narrow interface with a fake.** Service-plane and status code shall
run on an ordinary laptop with no radios present. A change nobody without
hardware can review is the failure this prevents.

Production code never imports from the test tree; the dependency runs one way.
Every fake is named in `test/flatsat/README.md` `[CI]`, and fixtures captured
from real hardware go in `test/fixtures/` with the node identifier, capture date
and image build recorded alongside them. A fixture whose provenance is unknown
is a number nobody can trace.

## Structure and simplicity

**A reader who does not write code should be able to navigate this repository.**
Every directory carries a `README.md` in plain language, or is named in its
parent's where a file of its own would be noise. Name a file for the question it
answers. If someone must read the code to learn what a directory is for, the
README failed and the README is what to fix. `[CI]`

**Every decision is findable from both ends.** Code that acts on a decision
cites its `FML-ADR-###` or `TBR-XXX-##` in a comment, and
`tools/gen-decision-index.sh` derives the reverse into `docs/decision-index.md`,
so an ADR can be read back to what implements it. Cited IDs are checked to
resolve `[CI]` and the index is checked for staleness `[CI]`. Never
hand-maintain the back-link: a hand-written `implemented-by` field rots, and
this program has already lost a hand-kept traceability matrix that way.

**A change explains itself in the log.** Conventional Commits, and a
`Refs: FML-ADR-### | TBR-XXX-##` trailer on any change that **adds or removes a
decision citation in code**, so that `git log --grep` answers "why did this
change" without anyone reading prose. Not on every change touching code: a
repository check that enforces a rule in this file serves no ADR, and a trailer
invented to satisfy a rule is a false link that outlives the commit. `[review]`,
reported by `tools/refs-report.sh` in every `tools/lint.sh` run, because a rule
nobody measures is one nobody keeps.

**Prefer the simplest thing that works.** No layer, wrapper, base class or
indirection before a second caller needs it. No module for work that is
anticipated rather than done. Complexity added early is defect surface no test
covers, and it is far easier to prevent than remove. A clever line that costs a
reader ten minutes is a defect in a repository maintained by volunteers in their
spare time.

## Conventions

- **Shell**: POSIX `sh` where possible, `bash` where not. `set -eu` and a usage
  comment. `shellcheck` and `shfmt -i 2 -ci` clean.
- **Python**: `ruff` lint and format, type hints on public functions.
- **YAML**: `yamllint`. **Ansible**: `ansible-lint`. **Markdown**:
  `markdownlint-cli2`; long lines in tables only.
- **OCI images by immutable digest**, never by tag, anywhere.
- **Commits**: Conventional Commits, a `Refs:` trailer where a decision is
  touched, and a `Signed-off-by` line. Short-lived branches into `main`.
- **Diagram sources are committed**, not only exports.
- **Generated files are never hand-edited**: `STATUS.md` by `tools/gen-status.sh`,
  the traceability matrix by `tools/gen-traceability.sh`, the decision index by
  `tools/gen-decision-index.sh`. CI fails on drift.
- **No badges.** A green badge is read as evidence of function; here it is not.
- **New binary format?** Check `.gitattributes` LFS coverage before committing.
- **Removing an item from `docs/NON-GOALS.md` needs an ADR.** That file is the
  record of what this program refuses to build, and scope returns quietly.

## How rules are kept

`[CI]` means a machine checks it and you cannot merge past it. `[review]` means
it holds only if you hold it. Unmarked rules are `[review]`.

**When you find a `[review]` rule was broken, make it `[CI]` in the same
change.** Every rule in this file that a machine now checks was added that way,
after something slipped past: every fake named (check 11), every directory
explained (check 12), nothing claiming hardware it has not met (check 13). A
rule nothing checks is a suggestion, and this repository has already shipped
three of them.

**A check nobody has watched fail is not a check.** Break the thing on purpose,
watch the check fire, then fix it. Do this when you write the check, not later.
And prefer one check that fires to two that say the same thing: a duplicate
makes both easier to ignore.

Never disable a linter wholesale to make something pass. Adjust the rule
deliberately and record why in the config.

## Characteristic failures

Real, from this repository. Recognise the shape.

1. **A document claimed more than the code did.** `test/flatsat/README.md` said
   it verified the CONOPS section 82 user flow. There was no authentication, no
   authorization and no request path; `admit()` accepted an empty string. The
   claim was written in good faith by someone who had just built the thing.
2. **A check that could never fire.** `validate()` compared a resolved EIRP
   against the profile field it had just been copied from. It read as a
   regulatory control and was unreachable code. Nobody had watched it fail.
3. **A fake answered the question the code was supposed to decide.**
   `FakeClock` returned `CREDIBLE` or `DEGRADED` directly, so the fail-closed
   tests asserted that a fixture agreed with itself. The suite looked thorough
   and could not have failed.

4. **A verification command did not cover what it claimed.** `tools/lint.sh`
   never ran `bats`, while `AGENTS.md` said a change was done when `lint.sh`
   passed. Two shell tests failed for days. They were also being read with
   `tail -1`, which prints the last test rather than the result, so the run
   looked green while its exit code was 1.

5. **A type that could not say "I cannot tell".** `FakeThermal` defaulted to
   `within_envelope=True`, so a node with no measured envelope asserted it was
   inside one. Fixing it, the replacement interface returned
   `throttling_reported() -> bool`, forcing a board with no throttle signal to
   answer `False` - the same claim, one field over. Four instances so far.
   Every reading a platform might be unable to provide is `T | None`.

The common shape: **something looked verified because nobody asked what would
have to break for the check to notice.** Ask it. And when you check, read the
signal that means success, not the one that looks like it.

Two of these now have machine checks, because both recurred. Coverage of
`mule/` is held at 100% `[CI]`, since the unreachable ones were single lines in
otherwise well-covered files and any threshold below would have hidden them.
And every reading in `mule/` needs a row in `docs/readings.md` `[CI]`, which is
the "how does this read on real hardware?" question asked in advance rather
than after the interface is wrong.

## Where the reasoning lives

This file states rules. These own the arguments behind them, and are the ones to
change when a rule turns out to be wrong.

| Subject | Document |
| --- | --- |
| The two-layer split, kernel and BSP, the compatibility set | `os/README.md`, `FML-ADR-040` |
| The flat-sat, its fakes and what a scenario proves | `test/flatsat/README.md` |
| What CI does and does not tell you | `test/README.md` |
| Evidence tiers and trade closure | `docs/evidence/README.md` |
| What this program refuses to build | `docs/NON-GOALS.md` |
| Secrets, capture and the threat model | `SECURITY.md`, `THREAT_MODEL.md` |
| Regulatory posture | `REGULATORY.md` |
| Contributor workflow and review | `CONTRIBUTING.md` |
