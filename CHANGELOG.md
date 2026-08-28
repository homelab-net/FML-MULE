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

### mule/sysfs.py: how a temperature actually reaches the node

`mule/thermal.py` decided what readings mean. Nothing produced them. Asking how
thermal would read on the selected hardware exposed two things.

**A defect, one field over from the one just fixed.** `throttling_reported()`
returned `bool`, so a board with no throttle signal had to answer `False` -
which is a claim that the node is *not* throttling, not the absence of a claim.
The same shape as `within_envelope=True` by default. It is now `bool | None`,
and `FakeThermal` defaults to `None`, because a scenario that did not script
throttling has not said the node is running unthrottled.

**A dead branch.** `temperatures_c` guarded `Path.glob` with `except OSError`.
`Path.glob` returns empty for a missing or non-directory root rather than
raising, so the branch was unreachable code that read like a safety net. Same
shape as the EIRP check. Removed, and a comment says why there is nothing to
guard.

#### What is decided, and what is not

- **Decided:** `/sys/class/thermal/thermal_zone<N>/temp` in millidegrees
  Celsius, `type` naming the zone. Kernel ABI, identical on every Debian-family
  node (`FML-ADR-022`), the same on a Pi and an x86 box. No trade gates it.
- **Per board:** which zone is the processor. Zone type strings are
  driver-supplied and unstandardised - `cpu-thermal`, `bcm2711_thermal`,
  `soc_thermal`. `TBR-HW-01` selects the board, so `ZoneMap` is configuration
  and is **empty today**: the node reports no temperatures rather than assuming
  `thermal_zone0` is its processor.
- **Not portable at all:** throttling. Linux has no general flag. The probe is
  injected; a platform with none reports `None`.
- **Not yet possible:** battery, enclosure and ambient readings need a BMS and
  an enclosure that do not exist.

Matching is on zone `type`, never zone number: numbering follows driver probe
order and moves between kernel versions, which is the class of bug that works on
the bench and fails after an update.

#### Added

- `mule/sysfs.py` and `test/flatsat/test_sysfs.py`. 100% covered, three new
  mutations, all caught. 37 of 37 overall.
- A test that reads `48250` as `48.25`, because getting millidegrees wrong
  faults a healthy machine instantly, and one that reads `-15000` as `-15.0`,
  because CONOPS section 61 makes cold first-order and a sign error would be
  wrong exactly when it matters most.

**Nothing here has run against real hardware.** The tests build a synthetic
sysfs tree, faithful to the documented interface and silent about any board.
This container exposes no `/sys/class/thermal` at all, which is itself why the
missing-root case is tested. A capture from a real node belongs in
`test/fixtures/` with node identifier, capture date and image build recorded.

### mule/thermal.py, and the last fake that reached a verdict

`FakeThermal` returned `within_envelope=True` by default and the node passed it
straight through, so **a node with no defined thermal envelope asserted it was
inside one**. `TBR-THERM-01` has not closed. There is no envelope. The node was
making a claim about a limit nobody has measured, which is the single thing this
repository exists to not do.

It was the last of three. `FakeClock` used to return `CREDIBLE` or `DEGRADED`
directly; `FakePower` returned `None` for runtime as a stub rather than a
refusal. Each is now a readings fake with the decision in `mule/`.

SAD section 25.7 draws the line for you: it lists processor, radio, battery,
enclosure and ambient temperature **and thermal throttling** among the things
`TBR-THERM-01` measures. Throttling is a reading - the compute element states
it. Being inside an envelope is a decision, because it compares a reading
against a limit. So the comparison is written now and the limits arrive later,
as `ThermalLimits`.

With no limits the state is `UNKNOWN`, however hot the node is. Not knowing is
not the same as being fine and not the same as failing. Throttling is still
reported in that state, because it is the one thermal fact available without a
measured envelope and withholding it would hide the clearest signal the node
has.

#### Added

- `mule/thermal.py`: `ThermalReadings`, `ThermalLimits` (no defaults, all
  `TBR-THERM-01`'s), `assess`. 100% covered, four new mutations, all caught.
- Per-sensor limits, because SAD section 25.7 measures the pack separately from
  the processor and one envelope across both would be wrong in a way that looks
  reasonable: comfortable for the processor, dangerous for the battery.
- A fault that **names the breached sensor**. "Too hot" is not an action; an
  operator told the battery is over its limit shades the pack, one told the
  processor is moves the node.
- `test/flatsat/test_thermal.py`, including that a sensor exactly at its
  critical figure is a breach. A limit is where the envelope ends, not the last
  temperature inside it.

#### Changed

- `ThermalState` left `test/flatsat/interfaces.py` for `mule/thermal.py`.
  `RadioState` is now the only interface left there, and the location note
  already says why it stays.
- `FakeThermal` reports a sensor mapping and a throttling flag. A sensor absent
  from the mapping is not fitted; one present with `None` is fitted and did not
  answer, and an operator would act differently on each.

34 of 34 mutations caught.

### mule/power.py: the procedure, written before the numbers exist

An open trade blocks a **value**, not a **decision**. That distinction had been
getting lost, and the repository's own rule already made it: code written now is
expected to be correct, exercised against fakes, and to work when it meets real
hardware; it just cannot be *known* to.

CONOPS sections 59 to 61 specify a complete procedure - pack capacity, reserve
margin, the service-host power penalty, cold derating - and are explicit that
the eight-hour figure is a planning objective and not a verified minimum.
`TBR-PWR-01` has measured none of the inputs. So the procedure is written now
and the inputs arrive later, as a `PowerModel` the caller supplies.

With no model the node says it cannot tell and names the trade. With one, it
answers. **Nothing in the node changes the day `TBR-PWR-01` closes**: two of the
thirteen CONOPS section 67 questions stop answering "cannot say" because
somebody measured a battery, not because somebody wrote software.

Three ways of not knowing are kept distinct, because an operator acts
differently on each: no pack fitted, no measured model, and a fitted pack that
cannot report its own charge. Collapsing them into one `None` would tell nobody
anything.

#### Added

- `mule/power.py`: `PowerReadings` (raw), `PowerModel` (measured inputs, no
  defaults, all `TBR-PWR-01`'s), and `assess`. 100% covered, four new mutations,
  all caught.
- `test/flatsat/test_power.py`, and scenarios showing the same node answering
  `None` today and a real estimate once a fixture model is supplied.
- Cold derating as a caller-supplied table, per CONOPS section 61. An
  uninstrumented pack gets no derating, which is optimistic and deliberately
  visible rather than a penalty invented for a temperature nobody read.

#### Changed

- `PowerState` left `test/flatsat/interfaces.py` for `mule/power.py` as
  `PowerReadings`, the same move time made: deciding how long a node will keep
  running is a judgement, and a fake making it is untestable.
- `FakePower` reports charge and pack temperature and reaches no conclusion.
- The fixture model deliberately does **not** produce the CONOPS eight-hour
  objective. A fixture landing on the objective would invite someone to read
  arithmetic on invented numbers as confirmation of it.

Writing the tests immediately caught a real bug: `assess` passed the
`pack_temperature_c` **method** rather than calling it, so cold derating never
ran.

### tools/lint.sh now runs the shell tests, which it never did

CI's first run on the repository found two `bats` tests failing. They had been
failing locally too, and were not noticed for two reasons that reinforced each
other.

`tools/lint.sh` did not run `bats`. `AGENTS.md` says a change is done when
`tools/lint.sh` passes, so the command the rules point at omitted the shell
tests entirely, and a contributor following the rules would never run them.

They were also being checked with `bats test/unit | tail -1`, which prints the
last test rather than the result. The last test passed, the exit code was 1,
and the output read as success. This is the same shape as reading a pipeline's
output instead of its status, which had already gone wrong once in this branch.

`lint.sh` now runs `bats`, and the `Done` rules say to read the exit code
rather than the last line. Recorded as the fourth characteristic failure.

#### Fixed

- **`gen-status reports a critical-path trade with no owner as a risk`** was
  matching a sentence `tools/gen-status.sh` stopped producing when its owner
  handling was corrected earlier in this branch. It now derives the unowned
  critical-path trades from the trade files and requires `STATUS.md` to name
  each, so a wording change cannot make it stale again. It also asserts at
  least one trade qualified, because the loop is worthless if none does.
- **`generated ADRs and trades pass validation`** asserted something check 10
  had made impossible: a freshly generated trade is `OPEN` and has no ITEP
  campaign, and check 10 correctly refuses it. That is the generator and the
  check both behaving properly, and the test's expectation was what was wrong.

  Split in two. A generated ADR must pass validation unmodified. A generated
  trade must fail, and the missing campaign must be the **only** failure -
  which is a stronger statement than the original, because it proves the
  generator produces otherwise-complete artifacts.

### TBR-TAK-01: the state classification, analysis half

`ITEP-C01` item 1, the campaign the plan says "can begin today, by one person,
with no budget". The ten SAD section 14.1 state categories are placed into the
three CONOPS section 26 classes with a justification each, the durable set is
named, and its partition and rejoin behaviour is described with a conflict
resolution rule.

**It does not close the trade**, and says so in its own first section. The
listed evidence also requires a different-node restore and the DataSync,
mission-package, certificate and map-cache tests, none of which has run. SAD
section 14.2 is explicit that support claimed rather than demonstrated is not
acceptance evidence; a classification derived from documentation says what state
*is*, not where an implementation *puts* it. The named owner is also still
`TBD-SRR`, and a trade closes only when a named owner accepts the evidence.

The artifact names no OpenTAKServer table, schema, endpoint or file path.
Writing one from memory would be inventing a specification of the most
plausible-looking kind: specific, confident and unsourced.

Five findings, of which three change downstream work:

- **Relational database state is not a class.** It is a container holding items
  from all three classes, and which rows fall where is a property of the
  implementation. This is why the empirical half is mandatory rather than
  desirable.
- **Database high availability alone cannot protect the durable set.**
  `FML-ADR-034` makes PostgreSQL preferred *conditional on* mission-critical
  state living in the SQL backend. At least two durable-set members - mission
  packages and uploaded files, and sole-copy map cache - are filesystem-shaped.
  If that holds empirically, `TBR-HA-01` is selecting a mechanism for a subset
  of the problem.
- **Timestamp conflict resolution is unavailable to this program.**
  `FML-ADR-042` permits a node to run with `TIME_DEGRADED`, so under
  last-writer-wins the node with the least trustworthy clock wins every conflict
  and wins it silently. `TBR-HA-01` must establish authority by something other
  than comparing wall-clock timestamps.

Two further findings: losing revocation state on failover is a trust validation
failing open, the same shape `FML-ADR-042` forbids for time; and cached map
tiles are not ephemeral in a deployment defined by the WAN being absent, because
the source that would serve a re-fetch is exactly what is unavailable.

### The Refs: rule gets measured instead of enforced

`Refs:` stays `[review]`, and `tools/refs-report.sh` is what makes that a
defensible position rather than a hopeful one. It prints the compliance rate on
every `tools/lint.sh` run and names the offenders. It never fails the build.

**The rule it measures was narrowed first, because the original was wrong.**
"`Refs:` on anything touching `mule/`, `tools/` or `os/`" would have demanded a
citation from `dc9bee9`, which added a repository check enforcing an `AGENTS.md`
rule and served no ADR. There was nothing legitimate to reference, and a trailer
invented to satisfy the rule is a false link that outlives the commit and looks
deliberate to every later reader.

The rule is now: a change that **adds or removes a decision citation in code**
records which decision. Checked against all 23 commits, it fires on 10 and
correctly stays silent on `dc9bee9`.

Current coverage is **8 of 10, 80%**. Both misses are scaffold commits from
before the convention existed.

#### Added

- `tools/refs-report.sh`, wired into `tools/lint.sh`. Defaults to
  `origin/main..HEAD` so it reports on work that can still be fixed rather than
  on history that cannot; `--all` for the whole record.

  It counts only identifiers that **resolve to a real decision**, because
  `test/unit/validate_docs.bats` plants a deliberately bogus one to prove a
  check fires, and counting that would have reported the test suite as a
  decision change forever.

  It also separates "recorded a different decision than the one whose citation
  changed" from "recorded nothing". The former is often correct and is shown
  rather than counted as a fault.

#### Changed

- `AGENTS.md` states the narrowed rule, says plainly why it is not "any change
  touching code", and names the report. A rule nobody measures is one nobody
  keeps.

### Finding a decision from the code, and the code from a decision

There was a rule for where code goes and none for how to get from a change back
to the reasoning behind it. Four directions were checked; three worked partly
and one did not exist.

- **Where does this live?** Covered: the placement table, one file per question,
  and check 12.
- **Why is this code like this?** Convention only. Code cites `FML-ADR-###` in
  comments, 25 citations across 7 decisions, and **nothing checked them**.
  A nonexistent decision id in a production docstring passed every linter and
  every check.
- **What implements this decision?** Did not exist. ADR frontmatter is
  `id title status date supersedes superseded-by trades verification`, with no
  link forward to code.
- **When and why did this change?** Partial. The `Refs:` trailer was optional
  and present in 13 of 21 commits, so `git log --grep` answered "why" about
  sixty per cent of the time.

#### Added

- `tools/gen-decision-index.sh` and `docs/decision-index.md`: the missing
  direction, **derived rather than maintained**. A hand-written `implemented-by`
  field would rot, and this program has already lost a hand-kept traceability
  matrix that way. Generated, checked for staleness in CI, and it cannot drift
  because nobody writes it.

  It separates code that **acts** on a decision from prose that **describes**
  one, because those are different claims. The first cut counted
  `test/stages/*/README.md` as implementation; a stage definition is a document,
  so the rule now keys on file type as well as path. The index currently reports
  28 of 48 decisions with no implementation, which is correct for pre-PDR and
  was previously invisible.

- Check 14 in `tools/validate-docs.sh`: every decision ID cited anywhere
  resolves to a real ADR or trade. Check 4 already did this for trades named in
  ADR frontmatter; this covers code, tooling, tests and prose. It immediately
  found a stale example ID in the trade template, and templates are now excluded
  because carrying an example ID is what a template is for.

#### Changed

- `AGENTS.md`: **every decision is findable from both ends**, and never
  hand-maintain the back-link. The `Refs:` trailer changes from optional to
  expected on anything touching `mule/`, `tools/` or `os/`, so `git log --grep`
  becomes a reliable index. Marked `[review]`: making CI reject a commit message
  is a workflow decision, and eight existing commits would fail it.
- `docs/README.md` gains a short "finding your way" table naming the three
  generated indexes and what each answers.

### AGENTS.md rewritten around when an agent needs each rule

The file had grown from 140 to 228 lines across five commits without anyone
deciding it should. It stated 34 rules, mixed inviolable constraints with
reference material and rationale, gave no way to tell which rules a machine
enforces, and never said what **done** means. It also broke its own rule: line
113 described the flat-sat's purpose as to "verify the end user experience"
while line 207 forbade writing "verified".

Rewritten to 196 lines. Nothing binding was dropped; every rule from the old
file was checked off against the new one before this landed.

**What changed structurally:**

- **A `Done` section**, which did not exist. Five conditions, including that new
  behaviour needs a test that fails without the change, and that any rule added
  is enforced by a check or explicitly said not to be.
- **A "Before you write" trigger table.** Rules are now indexed by the moment
  they apply - about to write a number, a claim, a requirement, a test
  assertion, a new check - rather than stated as principles to be remembered.
- **Enforcement markers.** Every rule is `[CI]` or `[review]`. `[CI]` means a
  machine refuses it; `[review]` means it holds only if you hold it. The
  distinction was previously invisible, and the unenforced rules are the ones
  that decayed.
- **"Characteristic failures"**, three real ones from this repository, with
  their common shape named: something looked verified because nobody asked what
  would have to break for a check to notice.
- **"Where the reasoning lives"**, a pointer table replacing about fifty lines
  that restated `os/README.md` and `test/flatsat/README.md`. A rule duplicated
  in two files drifts, and drift is this repository's chief pathology.

**The doctrine that keeps it honest:** when a `[review]` rule is found broken,
make it `[CI]` in the same change. A check nobody has watched fail is not a
check. Prefer one check that fires to two that say the same thing.

#### Added

- Check 13 in `tools/validate-docs.sh`: nothing claims `HARDWARE-VERIFIED`
  while nothing has met hardware. Written because marking that rule `[CI]`
  without a check would have been the exact failure the file documents. It
  steps aside once real evidence lands, and says so.

A first draft of check 13 also re-checked trade closure, until running it showed
two failures for one problem - check 7 already covers that. The duplicate was
removed rather than kept.

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
