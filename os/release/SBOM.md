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

`FML-ADR-081` selects CycloneDX 1.6 JSON for the Debian development image. The
selection does not extend to radio firmware or later OCI service images until
their own package and release decisions identify the complete inputs.

## Generator

The development builder uses Debian `debsbom` version
`0.10.1-1~bpo13+1` from same-time `trixie-backports`. It runs from mkosi's
separately locked tools tree against the completed target root, never from the
target itself. `tools/validate-image-root.py` compares the SBOM to the installed
dpkg set, requires source-package components and Debian copyright files, and
writes a machine-readable exception for every package without a normalized
declared licence.

`FML-ADR-083` adds one source-built component outside dpkg: `fml-mule==0.0.1`.
`tools/add-runtime-sbom.py` reads that distribution from the completed root and
adds its installed code, metadata, schema and native-unit digest to the same
CycloneDX document. The built-root validator recomputes the digest and rejects
a missing, duplicate or stale runtime component.

Requirements on whatever is chosen:

- Reads the built image, not the manifest.
- Covers the out-of-tree driver and the radio firmware, which are the
  components most likely to be missed by a generic tool because they did not
  arrive through the package manager.
- Records the kernel and its patch set, cross-referencing `docs/forks/`.
- Runs unattended as part of the build, because an SBOM that requires a manual
  step will be skipped on the release that most needs it.

The first two requirements are implemented for the Debian package closure.
Out-of-tree drivers and radio firmware remain outside this development image
and must extend the SBOM when `TBR-LINUX-01` selects them.

## What an SBOM does not give

It is an inventory, not an assurance. Knowing what is in a build says nothing
about whether those components are trustworthy, correctly configured, or free
of vulnerabilities nobody has published yet. `THREAT_MODEL.md` records that
pinning gives reproducibility and a reviewable change, not trustworthiness of
the pinned artifact. The same applies here.
