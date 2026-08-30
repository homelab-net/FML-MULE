---
id: FML-ADR-058
title: Development toolchain versions are pinned in a lock file
status: SELECTED
date: 2026-08-29
supersedes: none
superseded-by: none
trades: []
verification: TBD
---

# FML-ADR-058 Development toolchain versions are pinned in a lock file

## Context

`tools/install-deps.sh` installs the toolchain `tools/lint.sh` runs. When it was
written it installed the Python tools unpinned, because
`.github/workflows/lint.yml` installed them unpinned and a helper script should
not invent a compatibility set that the authoritative list does not have.

That left the linters as the only part of this repository's verification with no
recorded version. The consequence is narrow and specific: `tools/lint.sh` passing
does not say which `ruff`, which `ansible-lint` or which `yamllint` it passed.
Two contributors, and continuous integration, can each run a different set and
each see green. When one of them later sees red, the first question is whether
the code changed or the linter did, and nothing in the repository answers it.

This is the failure this program keeps finding in itself, in its usual shape: a
signal that looks like success while saying less than the reader assumes. The
repository already refuses it elsewhere. `FML-ADR-040` promotes kernel, driver,
firmware and userspace as one tested compatibility set. Container images are
referenced by immutable digest and never by tag, anywhere. `shfmt` is fetched at
a pinned version and verified against a recorded SHA-256. The development
toolchain was the remaining exception, and it was an exception by omission
rather than by decision.

Linters are not a neutral case. A new release of a linter adds rules. A tree
that passed on Monday fails on Tuesday with no commit in between, and the
failure arrives on whichever contributor happens to install next. That is a
build that breaks for reasons no diff explains.

Four options were on the table.

**Leave it unpinned.** Rejected. It is the current state, and the argument for
it, that the workflow does not pin either, describes the problem rather than
justifying it.

**Pin the direct dependencies only.** Rejected. Eight pinned packages pulling
twenty-eight unpinned transitive ones reproduces the same failure one layer
down, and `ansible-lint` in particular moves with its dependencies.

**Pin the fully resolved set.** Selected. It records what was actually
exercised rather than what someone believed would work.

**Pin the fully resolved set by hash.** Not selected now; see the accepted cost.

## Decision

The Python development toolchain **shall** be installed from a lock file,
`tools/requirements-dev.txt`, which records every package in the resolved set at
an exact version.

`tools/install-deps.sh` **shall** install from that file and from no other
source of versions. `.github/workflows/lint.yml` **shall** obtain its toolchain
by calling `tools/install-deps.sh`, and **shall not** restate the package list
or any version, so that the set continuous integration runs is the set a
contributor runs and the two cannot drift.

The interpreter **shall** be the version the lock was resolved against, in
continuous integration as on a contributor's machine.

The lock file **shall** be regenerated from an environment that has been
exercised, by running `tools/lint.sh` to completion and capturing the resolved
set from it. It **shall not** be edited by hand to add, remove or adjust a
version.

Refreshing the lock is a change like any other: a commit, a pull request, and a
green run. It is not automatic, consistent with the dependency policy in
`CONTRIBUTING.md`, which opens update proposals and never auto-merges them.

## Status

`SELECTED`.

Implementation depends on it: `tools/install-deps.sh` reads the file, and
changing where toolchain versions come from requires a superseding ADR.

## Consequences

`tools/lint.sh` passing now identifies what passed. A contributor and
continuous integration install the same thirty-six packages, and a disagreement
between them is a real disagreement rather than an artifact of when each last
installed.

Toolchain updates become visible. A linter version change appears as a diff in
a reviewed file instead of arriving silently with whoever installs next. That is
the property `FML-ADR-040` asks for on the runtime side, applied to the tooling
side.

What becomes harder. The lock file has to be refreshed by a person, and nothing
in this repository reminds anyone to do it. A pinned linter goes stale: rules
added upstream do not run here until someone updates the file, so this decision
trades a class of surprise failure for a class of silent omission. The
repository will hold a toolchain that is correct and old, and nobody will notice
until they read the file.

The lock was resolved on Python 3.13, which is what Debian stable ships and so
what `FML-ADR-022` implies a contributor runs. Continuous integration is pinned
to the same version for this reason: a resolved set is not guaranteed to install
on an interpreter it was not resolved against, and CI previously ran 3.11. That
alignment is part of this decision rather than incidental to it.

The set was resolved on Debian `x86_64`, and a package carrying compiled
extensions can have wheels for one architecture and not another. Because the
compute element is unselected but expected to be an `arm64` board,
`tools/check-toolchain-arm64.sh` asks on every continuous integration run
whether every pinned package has an `aarch64` wheel and whether the pinned
`arm64` binaries are published at the digests recorded for them. A lock refresh
that loses `arm64` support fails there rather than on the first board somebody
unpacks.

That check proves resolvability and nothing more. Nothing in this repository
executes an `arm64` binary, so the toolchain is **not** known to work there,
only to be installable. The lock may still need splitting per architecture if
the two ever diverge in a way one file cannot express.

Nothing about the node changes. This decision concerns the contributor's
machine. It creates no obligation on the image, the compatibility set, or a
volunteer in the field.

## Accepted cost

Two, both real.

**The toolchain will lag upstream.** The specific thing someone will later
argue was a mistake is a security fix that sat unapplied in a pinned linter for
months because refreshing the lock was nobody's task. The lag is at least no
longer invisible: `.github/dependabot.yml` opens a monthly proposal against the
lock, which is read as a staleness report rather than applied as written, since
a version changed in isolation is a set nobody resolved. That reports the
problem; it does not do the work, and nobody is assigned the work.

The counter-argument is that these tools read this repository's
own source on a contributor's machine and do not run on the node, so the
exposure is a developer workstation rather than a deployed system. That is a
smaller claim than "this is safe", and it is deliberately the only claim made.

**Exact versions are not hashes.** `==` pins fix the version, not the artifact.
The Python Package Index does not permit a released version's files to be
replaced, which makes the pin stable in ordinary practice, but it is a weaker
guarantee than the digest pinning this repository requires of container images
and the SHA-256 it requires of the `shfmt` download. Hash pinning was not taken
because it requires pinning the full transitive closure with `--require-hashes`
and a generator to maintain it, and no such tooling is present. This is an
inconsistency with the repository's own standard, recorded here rather than
left for a reader to notice.

## Fallback

Two directions, depending on which cost bites.

If the lock proves too stale to be useful, delete the pins and install
unversioned, returning to the previous state at the cost of reintroducing the
drift described above. The signal to do this is a contributor finding a defect
the current upstream linter would have caught.

If the pin proves too weak, move to a hash-pinned lock generated by a tool that
maintains the transitive closure. The signal is any evidence of index or
artifact tampering affecting a package in the set, and the cost is the
generator and the discipline to run it.

## Superseded by

None.

## Verification dependency

`TBD`, and no trade gates it.

There is no test stage, because no stage exercises a contributor's machine.
Verification is continuous instead: every continuous integration run installs
from the lock file and either resolves and lints clean or fails. A lock file
that cannot be installed is a build failure on the next run rather than a defect
that waits for a stage.

What that does **not** verify is that the pinned versions are the right ones.
Dependabot reports when they are behind, which is a weaker thing than knowing
they are correct: nothing here establishes that the pinned linters are the ones
this repository ought to be running, only that they resolve, install and pass.
That is the reason this section is `TBD` rather than a stage number.
