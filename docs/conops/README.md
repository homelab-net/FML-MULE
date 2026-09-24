# Concept of operations

**Status: BASELINE, pending stakeholder signature (CONOPS section 87).**

| File | Contents |
| --- | --- |
| `FML-MULE-CONOPS-v1.2.txt` | The controlling operational concept. v1.1 plus approved CCR-03 and accepted CCR-05. |
| `FML-MULE-CONOPS-v1.1.txt` | The previous issue, retained. CCR-04 only. |

The CONOPS is the **controlling subsystem operational concept**. Every
requirement in this program traces back to it, and the SAD in
`docs/architecture/` is derived from it.

## Why it is a `.txt` file

The CONOPS is issued as a plain-text controlled document, and it is stored here
byte-for-byte as issued. It is not reformatted into Markdown.

Converting a baselined controlled document to satisfy this repository's house
style would alter an artifact that is under the change control defined in its
own section 86, and would put transcription drift between the copy here and the
copy the signatories approved. The markdownlint configuration excludes it for
the same reason.

## Transcription integrity

The document carries its own audit figure. v1.2 has **185** `[SHALL]`
markers. v1.1 remains **151**.

```sh
grep -c '\[SHALL\]' docs/conops/FML-MULE-CONOPS-v1.2.txt   # expect 185
grep -c '\[SHALL\]' docs/conops/FML-MULE-CONOPS-v1.1.txt   # expect 151
```

That check passes on the copy in this repository. It is not proof of a perfect
transcription, but a dropped or duplicated clause changes the count, so it
catches the most likely class of error.

Per SAD section 35.4, a second reviewer must still confirm quoted CONOPS text
against the controlled source and record reviewer and date. That review has
**not** been performed on this transcription.

## Modal verbs

Section 0.2 fixes the meaning of three terms, and downstream documents preserve
them:

- **shall** - binding, decomposed into verifiable TRD requirements, appears in
  the Verification Matrix, and cannot be dropped downstream without a change
  request.
- **should** - preferred. Waiverable in the SAD or TRD with recorded rationale.
- **may** - permitted. Creates no obligation and no verification requirement.

Binding clauses are marked inline as `[SHALL]` to support extraction.

## What the CONOPS governs

- What MULE is for, and the operational situations it serves (sections 1-4).
- The user and organizational roles, and what each may and may not do
  (section 7).
- The service criticality model S0 through S3 (section 9).
- Identity, trust, revocation under partition, and the audit boundary
  (sections 13-18).
- The TAK operating concept, state classes, continuity, and split-brain safety
  (sections 20-31).
- The bearer set and RF coexistence priority (sections 32-38).
- Privacy, retention, and third-party data (sections 55-58).
- Power, sustainment, and cold weather (sections 59-63).
- The **13 qualification stages** (section 78), mirrored in `test/stages/`.
- The **58 operational success criteria** (section 79) and the verification
  traceability matrix that maps them to stages (section 85). These are
  transcribed as structured requirements in
  `docs/verification/requirements.md`.
- What is deliberately out of scope (section 81), seeded into
  `docs/NON-GOALS.md`.

## Change control

Section 86 governs. After signature:

- A change request records the section, current text, proposed text,
  operational rationale, downstream documents affected, verification impact
  against section 85, and approval.
- Editorial corrections that alter no `[SHALL]`, no section 79 criterion and no
  scope boundary are a point revision (`v1.02`).
- Adding, removing or altering a `[SHALL]`, a section 79 criterion, a section 78
  stage, or a section 81 exclusion requires a **minor version increment**
  and stakeholder re-approval. v1.2 is that increment for `CCR-03` and `CCR-05`.

Do not edit an issued version in place. The next version is a new file. The
previous file stays, so the copy that was reviewed is still the copy under
that name.

## Known open item

**PBCR-01.** The CONOPS deliberately generalizes the parent Homelab assumption
that TAK and communications-gateway functions are hosted only on NOMAD. That
change is recorded in `docs/change-requests/PBCR-01-field-service-plane.md` and
must be actioned before parent-system integration baseline closure.
