# GAP-09B execution card

## Finding and authority

- **Finding:** GAP-09B, reproducible base image (P1).
- **Decision served:** `FML-ADR-079`.
- **Related records:** `FML-ADR-022`, `FML-ADR-040`, `TBR-LINUX-01`,
  `TBR-HW-01`, GAP-09A, and OSS-01.
- **Owner approval:** retain Debian 13 and use Debian mkosi `25.3-7`, approved
  by the Program Owner in the Codex thread on 2026-09-12.

## Exact scope

Create the source-controlled mechanism for an uncompressed, bootable, raw GPT
Debian 13 x86-64 development image. Pin the builder artifact and upstream
source identity, use a dated signed Debian snapshot, distinguish initial cache
population from a network-forbidden rebuild, and reject incomplete inputs.

Do not select the GAP-09C package set, build from the current lab machine's
state, add credentials, select production hardware, decide rollback, render
networking, or deploy services.

## Versioned verification contract

GAP-09B is complete when all of the following hold:

1. An ADR records the owner-approved mechanism and its development-only scope.
2. The Debian builder package version, package SHA-256, upstream commit, signed
   tag object, dated repository snapshot, architecture, deterministic disk
   seed, image identity, manifest format, activated tools-tree source, and
   source-date epoch are source-controlled.
3. A validator rejects a floating builder version, live mirror, disabled key
   check, or mkosi configuration that differs from the governed inputs.
4. A build wrapper offers `--check`, `--populate-cache`, and `--offline`; the
   offline mode requests `CacheOnly=always` and no mode can build with an empty
   package manifest.
5. mkosi enters the OSS-01 corpus with immutable artifacts, license, security,
   maintenance, privilege, update, and exit-strategy records.
6. The complete repository gate passes with no skipped checks and a separate
   reviewer authenticates the exact implementation commit.

Actual package closure, SBOM, two-build image identity, network-unavailable
rebuild, and VM boot are GAP-09C acceptance, not evidence claimed by this card.

## Failing-first and red-team plan

- Run the new prior-art requirement test before registering mkosi; require it to
  fail because the selected builder is absent.
- Run the new image-validator and build-wrapper tests before implementation;
  require both to fail because their files are absent.
- Replace the snapshot mirror with the live Debian mirror, disable key checking,
  and restore the random disk seed in a temporary copy; require the validator
  to reject all three.
- Add the obsolete `Compression` key; require the governed v25.3 setting list to
  reject it even on a host without mkosi installed.
- Replace the exact builder version with `latest`; require rejection.
- Attempt a build with the empty package manifest; require refusal before root
  or tool checks.
- Inspect the patch for credentials, identifiers, mutable refs, and claims that
  an image was built or hardware was qualified.

## Rollback and completion

Revert the ADR, build files, prior-art record, validator, wrapper, tests, and
documentation as one change. No device state or produced artifact changes.
Closure requires independent review and a valid closure packet.
