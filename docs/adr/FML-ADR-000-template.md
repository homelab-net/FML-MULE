---
id: FML-ADR-000
title: Template, not a decision
status: RETIRED
date: TBD
supersedes: none
superseded-by: none
trades: []
verification: TBD
---

# FML-ADR-000 Template, not a decision

This file is the template every ADR is created from. It is numbered 000 and
carries status `RETIRED` so that it never reads as an active decision and so
that its ID is consumed and cannot be issued to a real one.

Create a new ADR with `tools/new-adr.sh "Title in sentence case"` rather than
copying this file by hand; the script allocates the next unused ID and rewrites
the frontmatter for you.

Delete this preamble and every instruction in the sections below when you fill
them in. Keep the section headings exactly as they are;
`tools/validate-docs.sh` requires all eight.

## Context

The situation that forced a decision. What constraint applied, what was in
tension, what alternatives were genuinely on the table and why they were
credible. A reader who was not present should finish this section understanding
why doing nothing was not an option.

State what was known at the time and what was not. If the decision was taken
with a trade still open, say so here.

## Decision

What was decided, in the active voice. Use `shall` where the decision binds
implementation, `should` where it is preferred and waiverable, `may` where it
permits without obligating. Do not use `will` or `must`.

One decision per ADR. If you find yourself writing "and also", that is a second
ADR.

## Status

The status value, spelled exactly as in `docs/adr/README.md`, matching the
frontmatter.

Then the qualifier the status requires:

- `CONDITIONAL` states the condition and what happens if it fails.
- `SELECTED TARGET` states what has not yet been demonstrated.
- `SELECTED PLANNING BASELINE` names the trade that will revisit it.
- `SELECTED PRINCIPLE` states what is decided and what is deliberately left to
  a later implementation ADR.

## Consequences

What follows from the decision. Include what becomes harder, what work it
creates, and what it forecloses. An ADR whose consequences are all favourable
has not been examined.

Cover, where applicable: effect on the build and promotion pipeline, on field
maintainability by a volunteer, on what a contributor without hardware can do,
and on the threat model.

## Accepted cost

What the program knowingly gives up by deciding this. Distinct from
consequences: this is the specific thing someone will later argue was a
mistake. Writing it down before they do is the point of the section.

If the honest answer is that the cost is not yet understood, write that, and
name the trade that will quantify it. Do not write `None`; there is always a
cost, and an ADR claiming otherwise is usually hiding one.

## Fallback

What happens if this turns out to be wrong. What the recovery looks like, what
it would cost, and what signal would tell the program to take it.

`None, this is structural` is a legitimate answer where the decision genuinely
cannot be unwound. Say it explicitly rather than leaving the section thin; a
structural decision with no fallback is exactly the kind a reader needs warning
about.

## Superseded by

An ADR ID, or `None`.

If this ADR supersedes an earlier one, record that in frontmatter under
`supersedes` and update the earlier ADR's `superseded-by` in the same change.
Both directions, always.

## Verification dependency

The test stage or evidence that would confirm the decision holds in practice,
referencing `test/stages/` where a stage exists.

`TBD` is acceptable at this stage of the program, but name the trade that will
define the verification. A decision that can never be checked is a decision
nobody can be wrong about, which is not a good property.
