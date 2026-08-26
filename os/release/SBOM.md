# Software bill of materials

An SBOM is a machine-readable inventory of everything in a build. This document
says where the program's SBOMs will live, what generates them, and what they
are for.

**No SBOM has been generated, because no image has been built.**

## Why this program wants one

Three specific uses, not general compliance:

1. **Answering "are we affected".** When a vulnerability is published in a
   library, the question is whether any deployed node contains it. Without an
   SBOM that question is answered by someone guessing from memory, and the
   answer is either "probably not" or a week of work.
2. **Making the compatibility set auditable.** `FML-ADR-040` promotes kernel,
   driver, firmware and userspace together. The SBOM is the evidence of what
   "together" actually meant for a given set.
3. **Licence obligations.** A repository published for other makers to build
   from redistributes other people's software. Knowing what, and under what
   terms, is a precondition for doing that honestly. Firmware redistribution
   terms are specifically `TBD`; see `os/kernel/PINS.md`.

## Where it lives

An SBOM is an artifact of a build, not a file maintained by hand.

- **Generated** during the image build, from the actual contents of the image
  rather than from the manifest that was intended to produce it. An SBOM
  derived from the input manifest cannot detect the difference between what was
  requested and what was installed, which is the difference that matters.
- **Published alongside the image artifact**, named to match it.
- **Retained** for as long as any node might still be running that set. Nodes
  are not updated promptly in this program; assume a long tail.

The SBOM is **not** committed to this repository for every build. It is a build
output. Where an SBOM is needed as evidence for a trade closure or an incident,
it goes under `docs/evidence/` with the rest of the evidence.

## Format

`TBD`. SPDX and CycloneDX are the obvious candidates. The choice is not
consequential enough to be a trade, but it should be recorded as an ADR when
made, because tooling downstream will depend on it.

## Generator

`TBD`. Depends on how the image is built, which depends on `TBR-LINUX-01`.

Requirements on whatever is chosen:

- Reads the built image, not the manifest.
- Covers the out-of-tree driver and the radio firmware, which are the
  components most likely to be missed by a generic tool because they did not
  arrive through the package manager.
- Records the kernel and its patch set, cross-referencing `docs/forks/`.
- Runs unattended as part of the build, because an SBOM that requires a manual
  step will be skipped on the release that most needs it.

## What an SBOM does not give

It is an inventory, not an assurance. Knowing what is in a build says nothing
about whether those components are trustworthy, correctly configured, or free
of vulnerabilities nobody has published yet. `THREAT_MODEL.md` records that
pinning gives reproducibility and a reviewable change, not trustworthiness of
the pinned artifact. The same applies here.
