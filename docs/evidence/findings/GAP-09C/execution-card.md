# GAP-09C execution card

## Decision served

`FML-ADR-081` selects the development-image package closure and provenance
policy. `FML-ADR-079` supplies the image mechanism and snapshot boundary.

## In scope

- Record the eight approved direct target packages separately from generated
  target and mkosi tools-tree locks.
- Authenticate same-time `trixie`, `trixie-security`, and builder-only
  `trixie-backports` inputs and retain every referenced package.
- Reject target closure drift, backports in the target, target-side `apt`, and
  target-side repository files.
- Generate CycloneDX JSON and a licence-exception report from the built root.
- Demonstrate two clean networked builds and one externally isolated cache-only
  build, identical raw-image SHA-256 values, and an offline QEMU/OVMF boot.
- Run the complete repository gate and obtain independent review of the exact
  implementation commit.

## Out of scope

- Production compute, kernel, BSP, radio, or firmware selection.
- Runtime, AP, ingress, mission-service, signing-key, update, or rollback
  implementation owned by later findings and open trades.
- Any claim about physical behavior or hardware verification.

## Required fail-first evidence

Before implementing each control, retain test output showing that the current
tree accepts an invalid or incomplete state. Mutation coverage shall include a
live source, disabled signature checking, a checksum mismatch, package-lock
drift, target backports, target `apt`, a target repository file, incomplete SBOM
coverage, and a missing copyright file.

## Acceptance evidence

Closure requires the generated lock and provenance artifacts, signed-metadata
and package checksum records, build logs, raw-image hashes, CycloneDX SBOM,
licence exceptions, QEMU transcript, complete gate output, and an independent
exact-commit verdict. Until those artifacts exist, GAP-09C remains OPEN.

## Stop conditions

Stop rather than relaxing the contract if the selected builder cannot consume
both authenticated archive families, the exact cache cannot rebuild with
external networking unavailable, raw image hashes differ, the image cannot
boot, or the SBOM cannot describe the installed root. A claimed environmental
or hardware block requires separate-agent qualification before it is recorded.
