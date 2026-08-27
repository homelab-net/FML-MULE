---
id: TBR-AREA-00
title: Short title in sentence case
status: OPEN
owner: TBD-SRR
area: AREA
priority: 99
function-owner: TBD
critical-path: false
depends-on: []
feeds: []
requires-hardware: TBD
evidence: docs/evidence/TBR-AREA-00/
adr: []
target-date: TBD-SRR
---

# TBR-AREA-00 Question in sentence case

Create a trade with `tools/new-trade.sh AREA "Question in sentence case"`
rather than copying this file; the script allocates the next unused number in
the area and rewrites the frontmatter and heading.

Filenames beginning with an underscore are skipped by `tools/validate-docs.sh`,
which is why this template does not fail validation. Delete every instruction
below when you fill the sections in, and keep all six headings.

## Question

One sentence, phrased as a question. If it needs a paragraph, it is more than
one trade and should be split.

## Why it matters

What breaks, stalls, or gets built wrong while this stays open. Name the
documents, decisions or components that are waiting. If nothing is waiting,
this may be a parking-lot item rather than a trade; see
`docs/parking-lot.md`.

## Options

What is genuinely being considered, including the option of doing nothing or
deferring. For each, note what would make it the right answer. Do not list an
option nobody would accept just to make the analysis look thorough.

## Closure evidence

Specifically what artifact would answer the question. Name the measurement, the
instrument class, the conditions, and the number of samples where that matters.
"We will test it" is not closure evidence. "Sustained throughput at three
recorded separations, measured with a traffic generator over one hour per
point, at a recorded ambient temperature" is.

Evidence is committed under `docs/evidence/<TRADE-ID>/`.

## Closure gate

The condition under which the program agrees the question is answered. Written
**before** the work, so the result cannot be graded against a standard invented
after seeing it.

State the threshold, or state that the gate is a comparison and name what is
being compared.

## Dependencies

- **Depends on:** trades that must close first, or `none`.
- **Feeds:** trades and decisions that consume this answer, or `none`.
- **Related decisions:** the `FML-ADR-###` entries this bears on, or `none`.
- **Validating stage:** the CONOPS section 78 stage, or `TBD`.
- **Requires hardware:** `yes`, `no` or `partly`, matching the
  `requires-hardware` frontmatter field. This determines whether a contributor
  without a node can work on it, which matters more than it looks.

## Frontmatter notes

`priority` is the SAD section 30.2 register position. `function-owner` is the
engineering function accountable for the trade. `owner` is a **named
individual**: SAD section 30.2 makes assigning one, plus a target date, to every
open TBR an SRR exit action, and `TBD-SRR` marks the gap explicitly rather than
hiding it behind a functional organization.
