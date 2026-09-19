# GAP-09C package and provenance implementation

**Date:** 2026-09-14. **Evidence tier:** UNVERIFIED build mechanism.

## Implemented

- `FML-ADR-081` records the owner-approved package, archive, and CycloneDX
  boundary.
- Separate package-manager sandboxes replace mkosi's generated live Debian
  sources with same-time `trixie`, `trixie-security`, and builder-only
  `trixie-backports` snapshots.
- The reviewed direct target intent contains eight packages. Authenticated APT
  metadata resolution produced a 97-package candidate target lock and a
  separate 414-package candidate tools-tree lock. The latter pins
  `debsbom` `0.10.1-1~bpo13+1` from backports.
- `tools/validate-image.py` parses the Deb822 inputs and requires the exact
  signed stanza sets. It rejects direct-intent drift, live, extra, trusted, or
  incorrectly scoped sources, incomplete lock provenance, target backports,
  target `apt`, target `debsbom`, generator drift, and mismatch between
  generated lists and locks.
- `mkosi.postinst` removes bootstrap-only `apt` and target repository files.
  `mkosi.finalize` generates CycloneDX 1.6 from the completed root, runs the
  installed-root validator, writes licence exceptions, and removes consumed APT
  metadata.
- `tools/validate-image-root.py` compares installed dpkg state with the target
  lock and rejects prohibited packages, target sources, missing copyright
  files, missing binary components, and missing source-package components. Its
  licence-exception output accepts only SPDX expression or SPDX-ID choices;
  name-only and malformed choices stay explicit exceptions.
- `tools/validate-package-cache.py` authenticates every retained `.deb` against
  the locks. The offline wrapper combines mkosi cache-only mode with a separate
  network namespace. The three-build runner uses separate fresh output and
  cache directories for both networked builds and replays one authenticated
  cache into a third fresh output directory. Build and QEMU paths both use the
  authenticated package-owned mkosi executable.

## Fail-first and mutation results

Before the implementation, the focused package/provenance test selection
failed four tests because the direct intent, scoped sources, and two locks did
not exist. The direct/source, prohibited-package/checksum, and missing-SBOM-tool
mutations then failed three tests because the prior validator accepted all
three defects. The built-root and cache-validator existence tests also failed
before those controls were added.

The implemented unit suite now passes mutations for a live or extra source,
source-level `Trusted: yes`, direct-set drift, target `apt`, a malformed package
SHA-256, a missing tools-tree `debsbom`, installed-set drift, a target repository
file, a missing copyright file, missing SBOM binary and source components,
non-SPDX licence choices, a missing cached package, and a corrupt cached
package. The offline wrapper fake records both `CacheOnly=always` and
`unshare --net`. The three-build fake proves clean cache/output separation,
image-drift rejection, required boot-marker handling, and resistance to a
shadow `mkosi` on `PATH`.

## Evidence not yet earned

No disk image, package cache, SBOM, licence-exception report, QEMU transcript,
or repeated raw-image hash was produced in this checkout. The two locks are
authenticated resolver outputs, not yet an accepted observation of installed
image contents. GAP-09C remains OPEN until the execution-card build runs,
installed state matches, two clean hashes and the isolated cache-only hash are
identical, QEMU reaches the selected systemd target without WAN, the full gate
passes, and an independent reviewer authenticates the exact commit.
