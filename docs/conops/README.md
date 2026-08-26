# Concept of operations

**Status: baselined. Controlling document not yet in this repository.**

The program's operational concept is baselined and is the source from which
every requirement in this program traces. It has not been transcribed here yet.

This README is a placeholder and says so. It is not a summary, and it is
deliberately not an attempt at one: a paraphrase written by someone working
from the acronyms would read like content, would be cited as though it were the
baseline, and would be wrong in ways nobody could detect. The controlling
document will be added here.

## What the CONOPS governs

- What MULE is for, and the operational situations it is meant to serve.
- Who operates it, with what training, and under what organisational structure.
- The PACE structure the equipment fits into, and what happens at each step
  down.
- Deployment patterns: how many nodes, how far apart, for how long, carried or
  emplaced.
- The endurance and portability requirements that `TBR-PWR-01` must satisfy.
- The environmental conditions the equipment is expected to survive, which
  `TBR-THERM-01` needs before it can state a worst-case ambient.
- What is expected to survive a node loss, which `TBR-TAK-01` needs before it
  can classify mission state.
- What operators do when the system fails, which is a procedure and not a
  feature; see `docs/NON-GOALS.md`.

Several open trades are blocked less by hardware than by the absence of a
stated requirement from this document. `TBR-PWR-01` cannot close without an
endurance requirement, and `TBR-THERM-01` cannot close without a worst-case
ambient. Transcribing the CONOPS unblocks work that no amount of hardware will.

## Document control

The CONOPS is a **controlling document**. When it lands here:

- It is baselined, and changes go through a **change request** rather than an
  ordinary pull request. A change request states what is changing, why, which
  requirements are affected, and which ADRs and trades are invalidated.
- A change that invalidates a `SELECTED` decision requires a superseding ADR,
  raised in the same change.
- Requirements carry the frontmatter described in `docs/README.md`, so
  traceability is generated rather than extracted by hand.
- Requirement IDs are permanent and never reused, on the same terms as ADR and
  trade IDs.
- The baseline version and date are recorded in the document itself, and a
  change to the baseline is a version increment, not an edit.

## Until then

Where an ADR or trade cites the CONOPS, it cites a document a reader cannot yet
open. That is an honest statement of the program's current state rather than a
gap to be filled with invention. Nothing in this repository should paraphrase
the CONOPS as though it were quoting it.
