# Prior art

Evaluations of external technologies the program considered: what fits the
architecture, what provides work it need not repeat, and what it deliberately
does not adopt and why.

This directory exists so a technology is not re-evaluated from scratch, and so a
decision *not* to adopt one is traceable rather than folklore. Each file names
the technology, states plainly whether it fits, separates "fits" from "provides
reusable ideas," and points at the trades or ADRs it bears on.

Fitting the existing ATAK/TAK architecture and the standard services the program
leverages, rather than building a parallel mechanism beside them, is `AGENTS.md`
rule 6. These evaluations are where that rule is applied to a specific candidate,
with the reasoning written down.

An evaluation here is not a decision. Where one concludes for or against
adopting something, the decision itself is an ADR or a `docs/NON-GOALS.md` entry;
this directory holds the assessment the decision would rest on.
