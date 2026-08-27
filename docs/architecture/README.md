# System architecture description

**Status: DRAFT v0.31, SRR package candidate.**

| File | Contents |
| --- | --- |
| `FML-MULE-SAD-v0.31.md` | The system architecture description, transcribed verbatim. |

The SAD translates the baselined CONOPS into an implementable architecture. It
is **the source of rationale for the ADR register** in `docs/adr/`: the ADRs
record each decision, its status and its consequences with a permanent
identifier, and cite the SAD section that argues it.

Neither replaces the other. A decision described only in the SAD is not citable;
a decision recorded only as an ADR has lost its reasoning.

## Verbatim, and excluded from markdownlint

The SAD is stored as issued. It is a controlled document, and reformatting it to
satisfy this repository's house style would alter a controlled artifact and put
drift between this copy and the one under review. The markdownlint configuration
excludes it deliberately and records why.

## Transcription integrity

The SAD states its own counts, which gives four independent checks on this copy:

```sh
grep -c '^| FML-ADR-0' docs/architecture/FML-MULE-SAD-v0.31.md   # 30 decisions
grep -c '^| C[0-9]'    docs/architecture/FML-MULE-SAD-v0.31.md   # 140 traced clauses
grep -c '^| \*\*TBR-'  docs/architecture/FML-MULE-SAD-v0.31.md   # 16 trades
grep -c '^| SR-0'      docs/architecture/FML-MULE-SAD-v0.31.md   # 11 source entries
```

All four pass. Section 35.1 states 140 traced clauses; section 0.8 lists 30
controlling decisions; section 30.2 lists 16 trades; section 34 lists 11
sources.

Section 35.4 still requires a second reviewer to confirm each `PRESENT` row
against the actual SAD text, and to confirm quoted CONOPS text against the
controlled v1.01 source. **That review has not been performed.**

## Identifier control, and what it means for this repository

Section 0.8 is load-bearing:

- The draft-local `AD-001` through `AD-020` labels used in SAD v0.1 and v0.2
  were reused when their meanings changed. **They are historical only and are
  not controlling identifiers.** Nothing in this repository cites them.
- Controlling decisions use the persistent `FML-ADR-###` namespace, and
  identifiers are never reused.
- SAD section numbers are **frozen** from v0.31 onward, because the RTM
  references them. New material uses subsections or appendices rather than
  renumbering.

`docs/adr/` holds one file per controlling decision, transcribed from the SAD
with its status and its supersession history.

## The one decision that is deliberately absent

The TAK automatic-recovery mechanism has **no ADR**, by decision. It remains
`TBR-HA-01` until a mechanism is selected, because selecting one before
`TBR-TAK-01` classifies the state would mean building an HA stack against an
unknown continuity boundary. See SAD sections 14.4 and 14.7.

## Structure

| SAD section | Subject |
| --- | --- |
| 0 | Document control, governing principles, decision identifier control |
| 1-2 | Architecture summary; the single-primary-compute selection and its fallback |
| 3-8 | Host platform, MANET, high-throughput bearer, HaLow, LoRa, RF coexistence |
| 9-12 | Mission service plane, logical isolation, service ingress, service authority |
| 13-14 | TAK architecture; persistent state and continuity |
| 15-18 | Service lifecycle, identity and trust, EUD admission, WAN overlay |
| 19-21 | Configuration, software supply chain, observability |
| 22-24.5 | Operator status, EMCON, external RF gateway, local time |
| 25 | Power, compute, thermal, storage, carrier, and physical host |
| 26-27.5 | Failure domains, security boundaries, data at rest and zeroize |
| 28-29.5 | Interface register, open-source map, MULE-original software inventory |
| 30-32 | SRR review, TBR register and dependency graph, risk review, entry assessment |
| 33-34 | Post-SRR engineering sequence; external source and evidence register |
| 35 | Clause-complete CONOPS traceability |

## Change control

The SAD is a controlled **draft**, not yet baselined. Changes are ordinary pull
requests reviewed by the relevant maintainer. A change that alters a `SELECTED`
decision still requires a superseding ADR: drafted status affects the document's
own stability, not the permanence of decisions taken from it.

Once baselined, it moves to the change-request process in
`docs/conops/README.md`.

Do not edit the transcribed document in place. A new SAD version is issued and
the file here is replaced.

## Diagrams

The SAD carries its diagrams as fenced `text` blocks, which diff and review as
text. Any new architecture diagram added by this repository uses Mermaid or
plain SVG for the same reason. See `docs/README.md`.
