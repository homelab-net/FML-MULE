# GAP-09B implementation evidence

**Date:** 2026-09-13. **Classification:** UNVERIFIED. No image was built or
booted by this increment.

## Failing-first observations

Before adding the selected builder to the prior-art corpus,
`test_selected_mkosi_builder_is_required` failed because `mkosi` was absent
from `REQUIRED_CANDIDATES`.

Before adding the image controls, `test_image_validator_exists` failed because
`tools/validate-image.py` did not exist, and `test_build_script_check_mode`
failed because `tools/build-image.sh` did not exist. These are the direct
pre-change failures for the behavior added by GAP-09B.

## Implemented controls

- `FML-ADR-079` records the approved planning baseline and fallback.
- `os/image/build-inputs.yml` records the builder and repository artifacts,
  target architecture, output contract, deterministic disk seed, tools-tree
  source, and deterministic time input.
- `os/image/mkosi.conf` describes a signed, dated Debian 13 x86-64 raw GPT
  image and cites the pinned external-tool documentation beside each setting.
- `tools/validate-image.py` compares both representations and rejects floating,
  unsigned, live-mirror, malformed-hash, and inconsistent inputs.
- `tools/build-image.sh` provides validation, cache-population, and offline
  entry points; it refuses to build until GAP-09C populates the package
  manifest.
- mkosi is an approved, immutable, owner-authorized record in the OSS-01
  corpus.

The downloaded Debian package matched its recorded SHA-256. Running that exact
package's `mkosi summary` found and corrected the obsolete `Compression`
setting name, then exposed mkosi's random default disk seed and host-dependent
tools-tree release. `CompressOutput=no`, a UUIDv5 seed derived from the ADR, and
the Debian 13 tools-tree release and snapshot are now explicit. A second exact
package parse accepted the configuration.

Parsing the wrapper's exact command line then showed that passing a `.raw`
suffix causes mkosi v25.3 to append a second `.raw`. The regression test first
failed with the resulting missing expected artifact; the wrapper now passes the
basename and verifies the single-suffix `mule-development.raw` output.

Independent source review also found that mkosi's target-side Debian source
writer still names live debug and security URLs even though `LocalMirror`
constrains build-time resolution. The evaluation now states that boundary
explicitly, and GAP-09C owns removal or replacement plus validation of the apt
sources retained inside the image.

The reviewer also found that pinned tools-tree metadata alone describes only a
fallback: without `ToolsTree=default`, mkosi still executes host programs. The
activation regression failed first on the missing setting. The governed tools
tree is now enabled explicitly, and its package closure remains GAP-09C work.

`ImageId` and `ManifestFormat` are now governed values rather than comments
beside unchecked literals. The wrapper reads the governed image identifier
instead of independently repeating it. The validator also rejects every
unknown mkosi setting in the four used sections, which makes the obsolete
`Compression` spelling fail in CI even when the exact mkosi package is absent.

## Evidence boundary

This increment proves repository enforcement only. It does not prove that the
selected package closure exists, that mkosi produces bit-identical images, that
the cache is complete, that the image boots, or that any physical device runs
it. Those statements require GAP-09C and later device evidence.
