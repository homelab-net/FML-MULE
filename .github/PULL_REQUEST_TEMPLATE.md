## What this changes

<!-- One or two sentences. What a reviewer needs to know before reading the
diff. -->

## Which ADR or trade does this affect

**Required.** A change that affects neither is either trivial or premature, and
saying which is part of the review.

- **Decision:** <!-- FML-ADR-### , or "none, trivial", or "none, this proposes
  a new decision" -->
- **Trade:** <!-- TBR-XXX-## , or "none" -->

If this closes a trade, give the evidence path under `docs/evidence/`. **A
trade does not close on document wording alone.**

- **Evidence:** <!-- docs/evidence/TBR-XXX-##/... , or "not a closure" -->

## Checks

- [ ] `tools/lint.sh` passes.
- [ ] `tools/validate-docs.sh` passes.
- [ ] If I changed ADR or trade frontmatter, I regenerated `STATUS.md` with
      `tools/gen-status.sh` and committed the result. I did not hand-edit it.
- [ ] Commits follow Conventional Commits and carry a `Signed-off-by` line
      (DCO). `git commit -s`.

## Rules this change respects

- [ ] **No invented specification.** Unknown values are `TBD` with the trade
      that will decide them, never a plausible-looking number.
- [ ] **No claim that anything is tested.** Unknown status is `UNVERIFIED`.
      No badges.
- [ ] **Nothing real is committed.** No key, certificate, credential, real
      callsign, real member identity, real deployment location, or captured
      operational data. Photographs have had their metadata stripped.
- [ ] **No mutable container image tag.** Images are referenced by immutable
      digest.
- [ ] **No region hardcoded.** Frequencies, channels and power come from a
      region profile under `regions/`.
- [ ] **I did not implement the placeholder services.**
      `services/status-aggregator/`, `services/mission-trust/`,
      `services/service-controller/` and `services/gateways/` hold a README
      and nothing else until their trades close.
- [ ] If this adds a binary or CAD format, `.gitattributes` already tracks it
      with Git LFS.
- [ ] If this carries an upstream patch, `docs/forks/` has an entry with a
      **named** owner.

## Hardware

- [ ] This change can be exercised without hardware, against fakes.

If it cannot, say who has verified it and on what. A change only its author can
exercise is a change only its author can review.

## Anything a reviewer should push back on

<!-- Where you were unsure, where you guessed, where you would like a second
opinion. This section is not a formality: a reviewer who knows where to look is
worth several who do not. -->
