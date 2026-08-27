# Change requests

Change requests against a **controlling document** or against the **parent
Homelab baseline**.

This is not the place for ordinary repository changes. An ordinary change is a
pull request. A change request is required when the change alters a document
that is under its own change control.

## Two kinds

**CONOPS change requests.** CONOPS section 86 governs. After signature, a change
to the CONOPS records the section affected, the current text, the proposed text,
the operational rationale, downstream documents affected, verification impact
against section 85, and approval.

- Editorial corrections that alter no `[SHALL]`, no section 79 criterion and no
  section 81 scope boundary are a **point revision** (`v1.02`).
- Adding, removing or altering a `[SHALL]`, a section 79 criterion, a section 78
  stage, or a section 81 exclusion requires a **minor version increment**
  (`v1.1`) and **stakeholder re-approval**.

**Parent-baseline change requests (`PBCR-###`).** Changes the MULE subsystem
requires in the parent Homelab baseline. These do not block MULE work; they
block parent-system integration baseline closure.

## Register

| ID | Subject | Status |
| --- | --- | --- |
| `PBCR-01` | TAK and communications-gateway allocation moves from NOMAD-only to the controlled Field Service Plane | `OPEN` |

## When a CONOPS change request is the right answer

Three places in the current baseline anticipate one, and say so rather than
leaving the program to discover it under pressure:

- **The 8-hour endurance objective.** SAD section 25.1: if `TBR-PWR-01` shows
  the architecture cannot meet it with acceptable pack mass, the program raises
  a change request against the objective **rather than conceal the problem in
  the battery BOM**.
- **The 60-second TAK recovery objective.** SAD section 14.6: if `TBR-TAK-01`
  shows it cannot be achieved without disproportionate complexity or unsafe
  authority semantics, the program raises a change request **rather than
  introduce an unjustified HA stack merely to preserve the number**.
- **Promoting anything off `docs/NON-GOALS.md`**, which is CONOPS section 81.

SAD section 33.5 states the general rule: **if measured evidence disproves a
CONOPS objective, the response is controlled CONOPS change, not hidden
architecture heroics.**
