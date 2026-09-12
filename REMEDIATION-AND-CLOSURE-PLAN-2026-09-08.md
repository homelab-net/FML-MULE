# FML-MULE Remediation and Verifiable Closure Plan

**Plan date:** 2026-09-08 **Revision:** 11 — OSS-01 progress recorded through 21 of 28 candidates
**Basis:** `CODEBASE-REPORT-2026-09-08.md` **Source commit:**
`d849ed40ff5bdbeef2def3eb6f982762768764c1` (verified against GitHub `main` on 2026-09-08) **Scope:**
Every code, integration, documentation, deployment, security, and workspace issue identified during
the 2026-09-08 inspection **Interpretation:** “Red hat” is treated as **red-team validation**:
deliberately attempt to defeat each fix before declaring it closed.

## Objective

Convert every inspection finding into a traceable work item with:

1. A preserved baseline failure or gap.
2. A bounded implementation change.
3. Positive, negative, boundary, and mutation tests where applicable.
4. Data collected from a clean and representative environment.
5. Independent review or execution of the acceptance procedure.
6. A durable evidence record linked to the governing requirement, decision, code change, test, and
   result.

No finding is closed merely because code was merged or a test passed once.

## Execution authority and mandatory user gates

This plan is written for execution by Codex or another coding agent. The active coding agent owns
implementation mechanics and evidence collection. The project owner (the user) retains all authority
over trades and architecture.

### Agent may proceed without additional architecture approval

The agent may:

- Inspect code, documentation, tests, history, generated artifacts, and public upstream projects.
- Reproduce existing failures using non-destructive tests.
- Create regression tests that encode behavior already unambiguously required by controlling
  documents.
- Fix an implementation that plainly violates an already approved schema, ADR, or requirement
  without changing that controlling decision.
- Run static analysis, unit tests, simulations, lint, mutation tests, and read-only diagnostics.
- Create comparison reports, benchmark harnesses, disposable prototypes, and draft decision packets.
- Correct factual documentation drift when the authoritative record is unambiguous.

### Agent must stop and obtain project-owner approval before execution

The agent must present the question to the project owner and wait before it:

- Opens, closes, resolves, supersedes, or materially changes a trade record.
- Creates, accepts, supersedes, or materially changes an architectural decision.
- Selects or replaces a protocol, network topology, bearer, hardware component, operating-system
  base, service implementation, storage model, trust model, ingress model, or high-availability
  mechanism.
- Defines previously unspecified product semantics, safety limits, security policy, regulatory
  behavior, acceptance thresholds, or failure behavior.
- Introduces an upstream project or library whose license, persistent data model, network behavior,
  update model, security boundary, or runtime privilege changes the architecture.
- Changes the root roadmap scope or treats deferred functionality as part of v0.0.1.
- Procures hardware, flashes a physical device, changes a remote deployment, alters credentials, or
  performs destructive cleanup without the separately required operational authorization.

Agents must not infer approval from silence, an existing prototype, a passing benchmark, or the fact
that an upstream project already made a similar choice.

### Required decision packet

Before any gated action, the agent will give the project owner a concise decision packet containing:

1. The exact decision or trade question.
2. The controlling requirement and affected repository records.
3. Viable options, including retaining the current design.
4. Relevant open-source prior art and measured results.
5. Compatibility, security, license, maintenance, resource, and migration consequences.
6. The agent's recommendation and reasons.
7. Reversibility and the smallest safe prototype.
8. The exact files and acceptance criteria that would change after approval.

Only the option explicitly approved by the project owner may be implemented. The approval and its
scope must be recorded in the associated ADR/trade history and closure evidence.

## Agent execution contract

Each task taken from this plan must be converted into an execution card before code changes begin.
An execution card contains:

- Finding and child-task identifier.
- Priority and current state.
- Implementing agent and independent verifier role.
- Controlling records and exact source locations.
- Inputs, assumptions, and dependencies.
- Files allowed to change.
- Explicit non-goals.
- User-decision gates and their status.
- Baseline reproduction command and expected result.
- Implementation steps small enough to review independently.
- Focused, integration, adversarial, and full-suite verification commands.
- Quantitative bounds for any words such as “all,” “repeated,” “large,” “clean,” or “reproducible.”
- Evidence artifact paths and secret-redaction requirements.
- Rollback/revert procedure for the code change.
- Definition of done.

If a required value is absent from the governing documents, the agent must not invent it. It must
prepare a decision packet and move the task to `AWAITING_USER_DECISION`.

## Open-source-first policy

FML-MULE will prefer proven open-source components and operating patterns over bespoke
implementations. “Fully leverage” means reuse the strongest compatible work while preserving
FML-MULE's requirements, evidence discipline, and security boundaries; it does not mean importing an
upstream architecture without evaluation and approval.

For every substantial component, agents must follow this order:

1. **Adopt:** use an upstream component unchanged and pinned if it meets the requirement.
2. **Configure or wrap:** retain upstream behavior and add only the integration boundary FML-MULE
   needs.
3. **Port a bounded component:** carry a clearly identified upstream implementation with provenance
   and an upstreaming plan.
4. **Reuse a pattern:** reproduce a proven operational approach when code reuse is incompatible.
5. **Build new:** only after the prior-art record demonstrates why the earlier options do not
   satisfy the requirement.

No upstream dependency enters the product merely because it is popular or functional in its native
environment.

### OSS intake record

Before adoption, each candidate requires a versioned intake record containing:

- Project and canonical upstream URL.
- Evaluated tag, commit, image digest, and evaluation date.
- License and compatibility review, including all bundled dependencies.
- Release cadence, maintainer activity, issue backlog, and bus-factor observations.
- Supported hardware and operating-system assumptions.
- CPU, memory, storage, startup, and power measurements on a representative target when relevant.
- Network ports, privileges, capabilities, mounts, secrets, and update behavior.
- Data formats and migration/backup behavior.
- Security history, published advisories, dependency/SBOM scan, and audit status.
- Exact FML-MULE requirement it could satisfy.
- Reuse mode: adopt, wrap, port, pattern-only, or reject.
- Integration prototype results and gaps.
- Exit strategy if upstream becomes unavailable or incompatible.
- User approval reference for any architectural adoption.

All adopted versions must be pinned. Floating tags, branch-head downloads, unauthenticated install
pipelines, and runtime self-update mechanisms are prohibited in release artifacts unless the project
owner explicitly approves a documented exception.

### Initial mandatory prior-art tracks

#### Project N.O.M.A.D

Official upstream:
[Project N.O.M.A.D repository](https://github.com/Crosstalk-Solutions/project-nomad)

Evaluate for offline content management, service discovery and presentation, health reporting,
content acquisition, Kiwix, Kolibri, ProtoMaps, and operator workflow patterns. Do not copy its
deployment wholesale: its documented design uses Docker, root/sudo installation, floating
image/update behavior in places, Docker-socket access, and intentionally provides no authentication.
Those differences must be measured against FML-MULE's rootless Podman, offline trust, deterministic
build, and least-privilege goals.

#### OpenMANET

Official upstreams: [OpenMANET firmware](https://github.com/OpenMANET/firmware) and
[openmanetd](https://github.com/OpenMANET/openmanetd)

Evaluate first for HaLow hardware support, Morse Micro driver/firmware integration, OpenWrt image
construction, 802.11s and batman-adv setup, node provisioning, addressing, DHCP/DNS, multicast/ATAK
behavior, range-test tooling, fault recovery, and field-operability patterns. Record the
architectural differences: current OpenMANET documentation uses OpenWrt, BATMAN-V, a flat bridged
mesh/client domain, and specific HaLow hardware, while current FML-MULE records select
Debian-oriented service hosting, BATMAN-IV, and different separation assumptions. Reuse or
convergence requires a user-approved trade decision.

#### Reticulum and NomadNet

Official upstreams: [Reticulum](https://github.com/markqvist/Reticulum) and
[NomadNet](https://github.com/markqvist/nomadnet)

Evaluate for encrypted delay-tolerant messaging, identity, heterogeneous bearer interfaces,
low-bandwidth routing, store-and-forward behavior, tooling, and degraded-mode communications. Treat
Reticulum as an alternate or adjacent networking stack, not as an assumed drop-in replacement for
the IP bearer plane. Its license contains use restrictions beyond a conventional permissive license
and therefore requires explicit legal/license review before distribution. NomadNet identifies itself
as beta and not externally security-audited; it may still provide useful patterns and test cases,
but that status must remain visible in evidence.

#### Existing FML-MULE candidates

Apply the same intake process to Martin, OpenTAKServer, Meshtastic, HAProxy, Podman, batman-adv,
hostapd, dnsmasq, Kiwix, Kolibri, ProtoMaps or PMTiles tooling, and any other proposed dependency.
Existing mention or bench use does not substitute for a pinned intake record and project-owner
approval where architecture is affected.

### Prior-art deliverables

Create and maintain:

- `docs/prior-art/registry.yml` as the machine-readable inventory.
- One evaluation document per candidate.
- Reproducible, non-production benchmark or prototype scripts.
- A requirement-to-candidate comparison matrix.
- A patch/fork ledger for every local divergence from upstream.
- An upstream contribution plan for generally useful fixes.
- Automated checks for license files, pins/digests, SBOM generation, and known-vulnerability review.

These paths are proposed by this plan. Because adding a new documentation class affects repository
structure, the agent must present the exact schema and integration changes to the project owner
before creating it in the repository.

## Closure protocol

Normal progress states:

`OPEN -> BASELINED -> FIX DESIGNED -> IMPLEMENTED -> RED-TEAMED -> VERIFIED -> CLOSED`

Control states:

- `AWAITING_USER_DECISION`: a trade or architectural choice has been presented and no implementation
  of that choice may proceed.
- `BLOCKED`: an approved dependency or required external capability is unavailable; the exact
  unblock condition must be recorded.
- `DEFERRED`: the project owner has moved the work outside the active milestone and recorded a
  re-entry condition.
- `ACCEPTED_RISK`: the project owner has explicitly accepted the documented residual risk without
  representing the issue as fixed.
- `REOPENED`: closure evidence failed reproduction, a regression occurred, or a closure assumption
  became false.

Only the project owner may move an architecture- or trade-bearing task out of
`AWAITING_USER_DECISION`, or place a finding into `DEFERRED` or `ACCEPTED_RISK`.

### Execution register

The implementing agent must keep this table current. “Agent” means the active Codex or coding-agent
session; “independent agent” means a separate review session that did not implement the change.

| ID      | Priority | Current state | Implementer | Verifier                                  | Mandatory user gate                                            |
| ------- | -------: | ------------- | ----------- | ----------------------------------------- | -------------------------------------------------------------- |
| BASE-01 |       P0 | CLOSED        | Codex       | `/root/gap01_verifier` passed             | Schema approved by project owner on 2026-09-09                 |
| BASE-02 |       P0 | CLOSED        | Codex       | `/root/gap01_verifier` passed             | None; verification did not change product behavior             |
| OSS-01  |       P0 | BASELINED     | Codex       | `/root/gap01_verifier` passed 21/28       | Registry structure approved by project owner on 2026-09-09     |
| GAP-01  |       P0 | VERIFIED      | Codex       | gap01_verifier passed                     | Decide size and nesting limits before closure                  |
| GAP-02  |       P0 | IMPLEMENTED   | Claude      | gap02_verifier                            | Approve catalog contract or service selection                  |
| GAP-03  |       P0 | CLOSED        | Claude      | gap030507_verifier                        | Approve any unspecified address semantics                      |
| GAP-04  |       P0 | CLOSED        | Claude      | gap0406_verifier                          | Approve capability/target model                                |
| GAP-05  |       P0 | CLOSED        | Claude      | gap030507_verifier                        | Approve unknown/failure semantics                              |
| GAP-06  |       P0 | CLOSED        | Claude      | gap0406_verifier                          | Approve status semantics and controlling ADR                   |
| GAP-07  |       P1 | CLOSED        | Claude      | gap030507_verifier                        | None unless required-check policy changes                      |
| GAP-08  |       P1 | CLOSED        | Claude      | gap08_verifier                            | Resolve any conflict between controlling records               |
| ENV-01  |       P0 | OPEN          | Agent       | Independent agent                         | Authorize remote ownership/destructive cleanup separately      |
| ENV-02  |       P3 | OPEN          | Agent       | Independent agent                         | Decide supported checkout platforms                            |
| GAP-09  |       P1 | OPEN          | Agent       | Independent agent plus milestone operator | Approve every component/architecture selection                 |
| HW-01   |       P2 | OPEN          | Agent       | Independent hardware operator             | Approve every hardware trade and test threshold                |
| GAP-10  |       P2 | OPEN          | Agent       | Independent security reviewer             | Approve every security and service architecture decision       |

No calendar deadlines are invented here. The agent executes in dependency and priority order and
reports measured progress; the project owner may add scheduling constraints.

### Required closure packet

Each closed finding must have one evidence document under the repository's evidence structure
containing:

- Finding identifier and exact scope.
- Governing CONOPS, SAD, ADR, trade, roadmap, or schema references.
- The pre-fix reproduction and its expected failure.
- Commit identifier and files changed.
- Test names and exact commands.
- Tool versions and relevant hardware/software environment.
- Raw or attached machine-readable results.
- Date, operator, and reviewer.
- Evidence classification: UNVERIFIED, SIMULATED, or HARDWARE-VERIFIED.
- Red-team attempts and outcomes.
- Residual risks and explicitly deferred work.
- Closure approval by someone other than the implementer for high-impact findings.
- SHA-256 hashes for retained raw artifacts and generated binaries/images.
- A redaction statement confirming that credentials, private keys, tokens, personally identifying
  data, and sensitive packet contents were not committed.
- The project-owner approval reference for every trade or architectural decision used.

Evidence output should be deterministic where practical. Generated status and traceability files
must be regenerated and committed without unexplained differences.

Raw evidence that cannot safely be committed must be stored in an owner-approved protected location.
The Git evidence record should contain a sanitized summary, artifact hash, retention location,
access classification, and reproduction instructions. Secret scanning is mandatory before evidence
is committed.

For P0, hardware, security, and milestone-acceptance findings, the verifier must inspect the diff,
rerun the focused reproduction and acceptance commands independently, and sign the closure packet.
Lower-priority documentation-only work may use independent diff review plus generated validation. An
agent may prepare a closure recommendation but may not self-review its own high-impact change.

### Universal closure gates

A finding may enter `CLOSED` only when all applicable gates pass:

- The original failure is represented by an automated regression test or a reproducible acceptance
  procedure.
- The proposed fix passes its focused tests.
- Full lint and test suites pass as the normal project user from a clean checkout.
- Relevant mutation tests or equivalent fault-injection tests prove the test can detect removal or
  inversion of the fix.
- Negative and malformed inputs fail safely and with useful diagnostics.
- Documentation and generated indexes agree with authoritative frontmatter.
- An independent reviewer confirms the evidence and reruns high-risk acceptance steps.
- Hardware claims are never closed using simulated evidence.

### Quantitative verification contract

An execution card must replace qualitative terms with a finite, versioned verification contract
before implementation:

- “All valid/invalid inputs” means the named fixture corpus plus the recorded property/fuzz
  generator, case budget, seed set, size limit, and nesting limit.
- “Repeated” means the recorded iteration count and permitted failure rate.
- “No resource leak” means named resources, measurement method, warm-up, baseline, duration, and
  permitted delta.
- “Full matrix” means the versioned set of requirement-derived combinations plus the stated pairwise
  or exhaustive generation method.
- “Clean checkout” means a named commit cloned into an empty path with no reused build, dependency,
  or test caches.
- “Reproducible image” states whether bit-for-bit identity is required; otherwise it names permitted
  nondeterministic fields and requires identical pinned inputs plus validated functional output.
- “Impossible status” means a prohibited combination in the project-owner-approved status truth
  table.

Where a bound changes product behavior or safety/security posture, the agent must obtain
project-owner approval. Pure test-budget choices may be proposed and recorded by the agent.

Intentional faults must be injected only in disposable fixtures, temporary branches, or disposable
worktrees. The agent must prove that no injected fault is present in the final diff or closure
evidence.

Proposed numerical trial counts in this plan are engineering confidence targets, not new product
requirements. The project owner must approve product thresholds; test-only budgets must be recorded
by the implementing agent and reviewed by the verifier.

## Phase 0: Establish an auditable baseline

### BASE-01 — Create a findings register

Create a machine-readable register assigning every item below an identifier, owner, reviewer,
severity, dependencies, current state, and evidence link. Extend document validation so every
`CLOSED` entry has a closure packet and every evidence link resolves.

**Acceptance evidence:** register validation passes; each finding in this plan appears exactly once;
no item is marked closed initially without existing qualifying evidence.

### BASE-02 — Capture a clean verification baseline

Repair the normal user's cache/workspace permissions first, then run the complete verification suite
from a clean checkout without root. Record the commit, operating system, Python version, dependency
versions, commands, exit codes, timing, coverage, mutation score, and test count.

**Red-team checks:** run with empty caches; run after deleting generated outputs; verify that a
deliberately broken test or lint fixture causes a nonzero result.

**Closure evidence:** one clean run with no permission warnings or ignored failures, plus proof that
the pipeline detects a deliberate temporary fault. The temporary fault must not be committed.

### OSS-01 — Build the prior-art and reuse register

Inventory Project N.O.M.A.D., OpenMANET, Reticulum, NomadNet, and the existing FML-MULE candidates
using the OSS intake record. Map each project to FML-MULE requirements and findings. Produce
reusable prototype commands without changing the product architecture.

**Required first outputs:** license/provenance assessment; architecture-difference matrix;
dependency/SBOM scan where buildable; version and digest pins; resource/privilege inventory;
candidate reuse mode; explicit questions requiring project-owner decisions.

**Red-team checks:** upstream disappears; tag is retargeted; image digest changes; license differs
between repository and bundled dependency; default deployment needs root or a privileged socket;
network behavior violates segmentation; project has no authentication; upgrade changes persistent
data.

**Closure gates:** every substantial planned component has a current intake record; every build-new
proposal cites evaluated alternatives; no upstream code is merged before its license and
architectural gates are approved; adopted components have pins, provenance, an exit strategy, and
regression coverage.

**Execution note, 2026-09-11:** 21 of 28 candidates have independently reviewed intake records.
Seven candidates remain `BASELINED`: Kiwix, Kolibri, ProtoMaps, PMTiles, Tailscale, the Morse Micro
driver, and the Morse Micro firmware. The evaluated hostap 2.12 artifact cannot be promoted with
runtime RADIUS configuration enabled until the upstream 2026-5 fix is present and its malformed
message regression test passes. Dnsmasq and step-ca remain `UNDECIDED` because the controlling
records select the required capability but do not select those implementations.

## Phase 1: Configuration and runtime correctness

### GAP-01 — Enforce the mission JSON schema

**Baseline:** `tools/gen-config.py` accepts the repository's invalid unknown-field example.

**User gate:** none for routing inputs through the already approved schema. Stop for approval if
implementation exposes an ambiguity in schema meaning, size limits, or runtime error policy.

**Actions:**

1. Add one canonical mission-loading and validation function using the declared Draft 2020-12
   schema.
2. Route the generator, flat-sat boot path, and any future runtime entry point through that
   function.
3. Keep repository-only example metadata checks separate from runtime mission validation.
4. Return stable, actionable validation errors including the failing JSON path.

**Red-team dataset:** unknown fields at every object level; wrong types; missing required fields;
malformed CIDRs; invalid service names; duplicate values where prohibited; deeply nested unexpected
data; oversized strings/documents; malformed JSON; valid minimal and full packages.

**Closure gates:** all valid fixtures pass; every invalid fixture fails for the intended reason; the
former bypass reproducer fails; no unhandled exception occurs; mutation testing catches removal of
the validation call and weakening of `additionalProperties` enforcement.

**Execution note, 2026-09-09:** the implementation is independently verified against FML-ADR-051 and
the declared schema. Focused tests, the full Python suite, the standalone validator, Ruff, and
mutations M71 and M72 passed in the independent session; the complete repository gate also passed.
GAP-01 is not closed because the schema declares no whole-document size, item-count, or nesting
budget. The project owner must decide whether to add limits or explicitly accept the current
unbounded schema before closure; the implementation does not invent those limits.

### GAP-02 — Enforce the service catalog

**Baseline:** the catalog is empty and arbitrary example service names are accepted.

**User gate:** present the minimum catalog contract and any service-selection consequences before
implementing the catalog schema or adding a service.

**Actions:**

1. Define the minimum catalog record schema needed by the roadmap milestone without inventing future
   service semantics.
2. Implement a catalog loader and validator.
3. Require every enabled mission service to resolve to exactly one enabled catalog record.
4. Reject duplicates, unknown services, disabled services, malformed records, and ambiguous aliases
   before boot.
5. Add the selected milestone service only when its actual deployment unit exists.

**Red-team dataset:** nonexistent names; case changes; Unicode lookalikes; path-like names;
duplicate records; disabled entries; missing unit references; a catalog entry pointing to an absent
Quadlet; multiple records with the same name.

**Closure gates:** 100% of accepted service references resolve uniquely; all adversarial entries
fail closed; removing catalog enforcement is caught by tests or mutation testing; catalog-to-unit
referential integrity is checked in CI.

### GAP-03 — Preserve and validate `address_prefix`

**Baseline:** a valid mission prefix disappears from generated configuration.

**User gate:** preserving an already required field needs no new trade. Any choice about IP family,
normalization, reserved ranges, or downstream allocation that is not explicit in FML-ADR-063 must be
approved first.

**Actions:** carry the value through the canonical mission model and resolved output; parse and
normalize it with an appropriate IP-network library; reject invalid, nonsensical, or disallowed
prefixes according to the governing decision rather than assumptions in code.

**Red-team dataset:** IPv4 and IPv6 inputs if both are allowed by the governing record; host bits
set; boundary prefix lengths; malformed CIDRs; overlapping reserved ranges if policy defines them;
missing values; string-encoding edge cases.

**Closure gates:** input-to-output round-trip tests show exact intended semantics; downstream
rendering consumes the field; omission or mutation of the field fails tests; a generated network
configuration demonstrates the selected prefix in use.

### GAP-04 — Make configuration resolution target-aware

**Baseline:** the AP-only v0.0.1 target cannot resolve because inactive HaLow, LoRa, and mesh values
remain TBD.

**User gate:** approve the capability/target model and its mapping to roadmap scope before
implementation.

**Actions:**

1. Define an explicit capability/target model tied to the roadmap and existing decisions.
2. Calculate required parameters from enabled capabilities rather than one global list.
3. Continue rejecting unresolved values that are required by the selected target.
4. Emit the selected target and active capabilities in resolved output for auditability.

**Red-team matrix:** AP-only; each individual bearer; supported combinations; an enabled bearer with
one required value missing; an inactive bearer with all values TBD; unknown target; contradictory
capability selections.

**Closure gates:** the full dependency matrix is automated; AP-only resolution succeeds without
inactive bearer values; enabling any bearer restores its complete validation requirements; mutation
tests detect accidental removal of a required parameter.

### GAP-05 — Handle unknown radio enumeration safely

**Baseline:** an allowed `None` result produces `TypeError` in `FlatSatNode._enumerated()`.

**User gate:** approve the semantic distinction and required state transition for unknown, empty,
and failed enumeration before production behavior changes.

**Actions:** define the semantic difference between “unknown,” “no radios,” and “read failure”;
preserve it through the radio adapter; produce a deliberate state/fault result rather than an
exception; align fakes with every permitted interface return.

**Red-team cases:** `None`; empty list; duplicated names; malformed names; intermittent command
failure; enumeration changing during bring-up; slow response; required radio disappearing after
boot.

**Closure gates:** no uncaught exception in any permitted interface state; deterministic fault/state
output; unit and integration coverage for every case; repeated fault injection produces no resource
leak or state corruption.

### GAP-06 — Define consistent operator-status semantics

**Baseline:** a booted node with a missing mandatory AP reports `operational=true` and
`state=FAULT`; unknown WAN state is collapsed to false by the flat-sat adapter.

**User gate:** the agent must submit the status vocabulary and truth table as an architecture
decision packet before changing status semantics.

**Actions:**

1. Establish the meaning of `operational`, `booted`, `ready`, `degraded`, and `fault` in a
   controlling ADR or existing architectural document.
2. Implement a single status truth table.
3. Preserve three-state values such as WAN `true`, `false`, and `unknown` through all layers.
4. Generate tests from the truth table where possible.

**Red-team cases:** every combination of boot, required AP, optional bearer, time credibility,
service readiness, WAN state, power fault, and thermal fault; contradictory or stale observations;
transitions into and out of faults.

**Closure gates:** exhaustive truth-table tests pass; no impossible status combinations are emitted;
external serialization preserves unknown values; property tests or mutation tests detect inverted
predicates.

## Phase 2: Continuous verification and documentation integrity

### GAP-07 — Correct integration-probe workflow triggers

**Baseline:** mesh and LoRa probes do not run when their scripts, configurations, or toolchain pins
change.

**User gate:** none for making existing probes run on their real dependencies. Any change to
required-check policy, evidence tier, or supported CI environment requires approval.

**Actions:** map every workflow to its dependency paths; add manual dispatch where absent; validate
workflow syntax; add a small automated changed-file/expected-workflow test or equivalent policy
check; ensure the main required checks surface probe status without claiming hardware coverage.

**Red-team cases:** changes to each bench script, workflow, configuration template, dependency
digest, and relevant runtime helper; unrelated documentation change; intentionally failing probe;
unavailable runner capability.

**Closure gates:** recorded CI run IDs demonstrate each relevant change triggers the intended
workflow and unrelated changes do not create unreasonable noise; an intentional failure blocks or
clearly fails the expected check; evidence remains classified SIMULATED.

### GAP-08 — Eliminate documentation decision drift

**Baseline:** roadmap, README, trade bodies, generated status, service documentation, package
metadata, and test documentation contradict authoritative state.

**User gate:** unambiguous synchronization with controlling records may proceed. Any conflict
between controlling records or change to a trade/architecture statement must be presented to the
project owner.

**Actions:**

1. Produce a contradiction inventory before editing.
2. Treat frontmatter and controlling decision records as the authoritative machine-readable state.
3. Correct all known stale TAK, trade-count, owner, testing, package, track-count,
   service-selection, and validator statements.
4. Extend validation for repeated structured claims: status, owner, counts, selected implementation,
   evidence tier, and generated-file freshness.
5. Replace broad prose such as “nothing tested” with precise tier-aware language.

**Red-team cases:** deliberately mismatch frontmatter/body status; change an owner; alter the
open-trade count; mark simulated work hardware-verified; stale a generated file; refer to a closed
trade as open.

**Closure gates:** zero known contradictions in the inventory; all generated documents reproduce
without diff; validator catches every injected mismatch; reviewer samples controlling documents
against README, roadmaps, services, and trade bodies.

### ENV-01 — Restore normal-user reproducibility

**Baseline:** root owns `.ruff_cache`, `.pytest_cache`, `.ansible`, and `.venv`, causing the
normal-user lint wrapper to fail or warn.

**User gate:** obtain separate operational approval before deleting, replacing, or changing
ownership of remote files.

**Actions:** inventory exact ownership and provenance; remove or correct only repository-local
generated state with explicit authorization; recreate dependencies as `mule1`; document the
supported execution user; make tooling use project-local writable cache paths.

**Red-team cases:** fresh clone; empty cache; read-only stale cache; invocation after an accidental
root-run; parallel tests.

**Closure gates:** dependency check, lint, tests, mutation tests, and generated-file checks all
complete as `mule1` with exit code zero and no permission warning; no source or evidence file is
made broadly writable.

### ENV-02 — Make cross-platform checkout behavior explicit

**Baseline:** the local Windows clone cannot reproduce the `CLAUDE.md` symlink and reports it
modified.

**User gate:** the project owner decides whether Windows-native checkout is a supported environment.

**Actions:** determine whether Windows-native checkout is supported. If supported, add an explicit
symlink/bootstrap strategy and CI coverage; if unsupported, document WSL/Linux as the required
checkout environment and prevent local artifacts from being confused with source changes.

**Closure gates:** a documented supported checkout produces a clean working tree, or the platform
limitation is explicitly declared and verified through the supported environment.

## Phase 3: Deliver the v0.0.1 vertical slice

### GAP-09 — Create a reproducible, deployable product path

This finding closes only when the narrow root-roadmap milestone exists end to end. It must not be
expanded to include deferred HaLow, mesh, LoRa, TAK, identity, or rollback work.

**User gate:** GAP-09 is an umbrella only. The agent must submit separate decision packets for
compute article, OS/image approach, runtime service boundary, AP network design, real service,
content format, DNS/ingress, and any deviation from current ADRs. Approval of one child does not
approve the others.

**Independently closable child tasks:**

- **GAP-09A — Development compute article:** compare existing hardware evidence and open-source
  supported targets; obtain project-owner selection; record that it is a development article, not
  production-qualified hardware.
- **GAP-09B — Reproducible base image:** compare the current Debian direction with proven image
  pipelines, including relevant Project N.O.M.A.D. and OpenMANET build lessons; obtain approval for
  any OS architecture change; implement pinned, offline-rebuildable inputs.
- **GAP-09C — Package manifest and provenance:** populate packages with versions/sources, generate
  an SBOM, verify licenses and signatures, and prove builds do not depend on floating branch heads
  or image tags.
- **GAP-09D — MULE runtime packaging:** install `mule`, add a bounded entry point and systemd unit,
  define privilege and failure behavior through existing decisions or a user-approved decision
  packet.
- **GAP-09E — AP-only network rendering:** produce hostapd, DHCP/DNS, and host-network configuration
  from validated target-aware inputs; obtain approval for any unspecified addressing, isolation, or
  failure semantics.
- **GAP-09F — One real service selection:** compare approved candidates and prior art. Martin,
  Project N.O.M.A.D. content components, Kiwix, and other candidates may be evaluated, but the
  project owner selects the milestone service and content format.
- **GAP-09G — Service deployment:** add the approved catalog record, pinned rootless Quadlet,
  content, health check, storage boundary, and only the DNS/ingress necessary for the approved
  phone-access path.
- **GAP-09H — Operator procedure:** produce build, install, boot, connect, access, diagnostics, and
  recovery instructions that a non-builder can follow without undocumented knowledge.
- **GAP-09I — Independent milestone acceptance:** execute and record the root-roadmap cold-start
  drill with someone other than the builder.

Each child receives its own execution card and closure packet. GAP-09 closes only after all required
children are closed; a child that the project owner declares unnecessary for the approved milestone
path must be marked `DEFERRED` with rationale rather than silently omitted.

**Red-team validation:** build from a fresh environment; corrupt or omit each required input; boot
without WAN; reboot repeatedly; remove the service image; use a malformed mission package; attempt
access before readiness; verify no excluded placeholder satisfies acceptance; inspect listening
ports and service privilege; power-cycle during startup; repeat with a second phone/browser if
available.

**Data to record:** source commit; dependency digests; image hash; build duration; image size;
boot-to-AP time; AP association result; DNS resolution result; service HTTP result; memory and
storage consumption; process ownership; listening sockets; systemd/Quadlet states; logs; cold-start
duration; operator observations; failure-recovery behavior.

**Closure gates:** a clean build reproduces the same declared inputs and image identity; the node
boots without WAN; a phone associates and reaches the named real service; no placeholder is
involved; the independent cold-start drill passes; evidence is correctly classified and linked to
the milestone.

## Phase 4: Resolve hardware and full-service risks

These items are later than v0.0.1 but remain open inspection findings. They must be tracked rather
than silently treated as part of the initial milestone.

### HW-01 — Establish a qualified hardware path

**User gate:** every hardware trade, procurement choice, regulatory interpretation, and pass/fail
threshold must be presented to the project owner before execution. Read-only research, comparison,
and non-destructive bench-harness preparation may proceed.

**Independently closable child tasks:**

- **HW-01A — RF consolidation decision packet:** complete the evidence comparison for RF-03 without
  selecting an option.
- **HW-01B — Carrier and M.2 decision packet:** compare supported layouts, including OpenMANET
  hardware and driver lessons.
- **HW-01C — Compute memory/storage decision packet:** measure candidate software stacks before
  recommending capacity.
- **HW-01D — Authorized procurement and article inventory:** procure only the project-owner-approved
  articles and record exact revisions/serial identifiers.
- **HW-01E — Linux/driver/firmware viability:** validate only the approved OS and radio stack, using
  pinned upstream sources and reproducible build records.
- **HW-01F — RF and coexistence characterization:** measure approved concurrent bearer cases with
  calibrated equipment.
- **HW-01G — Power and runtime characterization:** measure startup, idle, representative load, peak,
  degraded supply, and shutdown behavior against approved thresholds.
- **HW-01H — Thermal characterization:** measure steady state, transient load, throttling, recovery,
  and environmental conditions against approved thresholds.
- **HW-01I — RTC/BMS and hardware-zone behavior:** inject observable faults and verify approved
  state transitions.
- **HW-01J — Regional profile evidence:** create the real US-915 profile only from approved
  regulatory interpretation and measured hardware capabilities.

Each child requires its own execution card and closure packet. Decision packets do not close
physical-validation children.

**Red-team validation:** cold and hot starts; maximum intended concurrent bearer load; degraded
supply; peripheral disconnect/reconnect; storage pressure; clock loss; thermal throttling; driver
reload; radio coexistence; repeated power cycles; operation with WAN absent.

**Data to record:** exact BOM and revisions; firmware and driver hashes; test setup calibration;
voltage/current traces; runtime; temperature traces; throttling; RF throughput and loss; coexistence
effects; boot reliability; fault logs; regulatory source references.

**Closure gates:** each hardware claim has physical measurements on the identified article;
pass/fail thresholds come from controlling requirements or an approved decision record; independent
reproduction is completed for safety- or mission-critical claims; evidence is labeled
HARDWARE-VERIFIED only when justified.

### GAP-10 — Implement and verify security/service boundaries

**Prerequisite decisions:** identity model, offline trust anchors, certificate issuance and
revocation, authorization policy, ingress boundary, OpenTAKServer state/HA mechanism, recovery
objectives, and at-rest key handling must be resolved in controlling records before implementation.

**User gate:** every prerequisite and child architecture decision must be presented separately to
the project owner. Approval to prototype or deploy one boundary does not approve the others.

**Independently closable child tasks:**

- **GAP-10A — Threat model and trust-zone decision:** document assets, actors, zones, data flows,
  misuse cases, offline constraints, and candidate controls; obtain approval before security
  architecture implementation.
- **GAP-10B — Identity and admission decision/implementation:** evaluate existing FML-MULE and
  Reticulum identity patterns plus other proven projects; implement only the approved model.
- **GAP-10C — Authorization model:** define and test subject, service, mission, role, denial, and
  audit semantics after approval.
- **GAP-10D — Offline TLS and revocation:** implement approved trust anchors, issuance, renewal,
  expiry, revocation, recovery, and clock-uncertainty behavior.
- **GAP-10E — Ingress trust boundary:** strip client-supplied identity headers, set trusted values,
  isolate backend ports, and verify network-zone enforcement.
- **GAP-10F — OpenTAKServer process deployment:** package and supervise `opentakserver`,
  `eud_handler`, and `cot_parser` as approved, pinned units.
- **GAP-10G — TAK durable state and HA:** implement the approved mechanism for SQL plus
  `config.yml`, CA data, and uploads without unapproved wall-clock conflict resolution.
- **GAP-10H — Backup, restore, and recovery:** prove integrity and approved recovery objectives
  independently of HA.
- **GAP-10I — At-rest secrets and keys:** implement the approved key custody, provisioning,
  rotation, backup, and destruction paths.
- **GAP-10J — Service controller and status aggregator:** reuse upstream health/supervision patterns
  where compatible and expose only approved semantics.
- **GAP-10K — Gateways and protocol boundaries:** treat every gateway as a separate threat and
  architecture boundary.
- **GAP-10L — Independent security review:** run the approved adversarial suite and document
  residual risk after all required children close.

Each child requires its own execution card, upstream intake where applicable, and closure packet.
GAP-10 remains open until the project owner has explicitly scoped which children belong to the
intended release and every in-scope child is closed.

**Red-team validation:** spoof `X-Ssl-Cert`; reach the app port directly; use expired, revoked,
untrusted, malformed, or future-dated credentials; replay admission; enumerate unauthorized
services; cross mission boundaries; operate with incorrect time; corrupt replicated state; interrupt
synchronization; restore from backup; inspect container privileges, mounts, secrets, network
namespaces, and listening sockets.

**Data to record:** packet captures; proxy and application logs; authorization decision logs; port
scans from each network zone; certificate-chain and revocation results; process/container
privileges; state-integrity hashes; recovery timing; backup/restore results; audit completeness.

**Closure gates:** spoofed identity headers never reach the trust boundary as authoritative input;
the application port is unreachable from untrusted zones; revoked and unauthorized identities fail
closed offline; authorized use succeeds; state recovery is demonstrated; tests cover clock
uncertainty; an independent security review confirms the threat cases and residual risks.

## Execution order and dependencies

1. `BASE-01`, `BASE-02`, and `ENV-01` establish trustworthy measurement.
2. `OSS-01` begins immediately as read-only research and continues as a gate for every substantial
   build-or-adopt choice.
3. `GAP-01` through `GAP-06` correct the configuration and runtime contract. The agent pauses at
   each listed user gate before changing unspecified semantics.
4. `GAP-07` and `GAP-08` make ongoing verification and reporting dependable.
5. `GAP-02`, `GAP-03`, and `GAP-04` are prerequisites for the v0.0.1 product slice.
6. `GAP-09A` through `GAP-09I` deliver the only currently scheduled milestone through separately
   approved and closable steps.
7. `HW-01A` through `HW-01J` supply decisions and physical evidence needed for later prototype and
   qualification claims.
8. `GAP-10A` through `GAP-10L` follow their individual user-approved architectural decisions and
   must not be presented as complete before adversarial validation.

Read-only prior-art evaluation may run ahead of a decision. Product implementation depending on that
decision may not.

## Increment integration and pre-HIL deployment gate

Each independently verified increment is merged to GitHub `main` only after its required CI checks
pass. The next increment begins from that updated `main` so the remediation history remains
reviewable and reproducible.

General deployment to the lab device waits until every pre-HIL remediation item and decision gate is
closed. A closure gate that explicitly requires real hardware is the exception: after the supporting
code is merged and green on `main`, the exact merged commit may be deployed to the lab solely for
that named HIL campaign. Record the device's before and after commit, the deployment inputs, the
commands run, and the resulting evidence. Do not advance any unrelated claim to `HARDWARE-VERIFIED`.

A hardware-gate deployment does not close the complete plan by itself. The plan closes only after
all in-scope HIL campaigns, hardware items, residual-risk dispositions, and closure packets pass
their own gates.

## Proposed work packages

### Work package A — Trustworthy inputs

`BASE-01`, `OSS-01`, `GAP-01`, `GAP-02`, `GAP-03`, and `GAP-04`.

**Exit result:** every accepted configuration is schema-valid, catalog-valid,
capability-appropriate, and complete for its selected target.

### Work package B — Deterministic runtime state

`GAP-05` and `GAP-06`.

**Exit result:** uncertain hardware observations and status combinations produce intentional, tested
states rather than crashes or contradictions.

### Work package C — Reproducible verification

`BASE-02`, `GAP-07`, `GAP-08`, `ENV-01`, and `ENV-02`.

**Exit result:** a normal-user clean checkout can reproduce checks, relevant changes trigger probes,
and documentation cannot silently contradict structured decision state.

### Work package D — First deployable node

`GAP-09A` through `GAP-09I`.

**Exit result:** the root-roadmap cold-start acceptance is independently demonstrated using a real
service.

### Work package E — Hardware and service qualification

`HW-01A` through `HW-01J`, and `GAP-10A` through `GAP-10L`.

**Exit result:** later capabilities advance only with controlling decisions, adversarial tests,
measured data, and correctly classified evidence.

## Change isolation and agent handoff

Every implementing agent must keep changes bounded to its execution card. Unrelated dirty-worktree
changes belong to the user and must be preserved. Architecture research, disposable prototypes, and
fault injection must not be mixed into a production implementation commit.

Before yielding or handing work to another agent, record:

- Finding/task identifier and current state.
- Branch/worktree and base commit.
- Changed files and whether each change is complete.
- Commands run, exit codes, and artifact locations.
- Decisions already approved, with exact scope.
- Questions awaiting project-owner approval.
- Known failures, residual risk, and next safe action.
- Confirmation that no credential or sensitive evidence was stored.

Implementation commits should be small enough to revert independently. Reverting a code change is an
engineering recovery action and does not imply product rollback functionality.

## Reporting cadence

For each work package:

- Record the baseline before implementation.
- Update the findings register when a state changes.
- Attach raw results rather than transcribing only conclusions.
- Publish a short verification summary containing failures as well as passes.
- Re-run generated status and traceability checks.
- Require reviewer sign-off before closing the package.
- Reopen a finding automatically if its regression test later fails or its closure evidence becomes
  irreproducible.
- Stop and send the project owner a decision packet whenever a trade or architecture question
  emerges, even if the agent has a preferred answer.

## Definition of completion for this plan

This plan is complete when every identifier is either:

- `CLOSED` with a complete, independently reviewable closure packet; or
- explicitly moved by the project owner to `DEFERRED` or `ACCEPTED_RISK` with rationale, risk,
  dependency, and re-entry or review criterion.

An empty test-results directory, a passing simulated test, merged code without deployment evidence,
or prose declaring success is not sufficient closure.

Architecture and trade records are never deemed approved merely because this plan is complete. Their
authority comes only from the project owner's explicit decisions.

## Primary open-source references checked for Revision 2

- [Project N.O.M.A.D. repository and deployment documentation](https://github.com/Crosstalk-Solutions/project-nomad)
- [OpenMANET documentation](https://github.com/OpenMANET/docs)
- [OpenMANET firmware](https://github.com/OpenMANET/firmware)
- [OpenMANET networking design](https://openmanet.github.io/docs/networking)
- [Reticulum repository](https://github.com/markqvist/Reticulum)
- [Reticulum manual](https://reticulum.network/manual/)
- [NomadNet repository and maturity warning](https://github.com/markqvist/nomadnet)

These links establish candidates and current upstream claims as of 2026-09-08. They do not
constitute an adoption decision.
