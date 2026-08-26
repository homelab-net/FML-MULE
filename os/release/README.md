# Release

How a candidate compatibility set becomes a deployable artifact.

**No release has ever been performed.** No image has been built, no set has
been promoted, and no node has been deployed. Everything below is process
definition, written before the first release so that the first release has a
process to follow.

## What is being released

Not a package, and not an image: a **compatibility set**. Kernel, out-of-tree
radio driver, radio firmware, and required userspace, versioned and promoted
together and never independently. See `FML-ADR-040` and `os/kernel/PINS.md`.

A change to any pin creates a new candidate set. There is no such thing as a
small change here.

## The promotion gate

A candidate set is promoted only after it has, on the target hardware block:

1. **Rebuilt all out-of-tree modules** against the candidate kernel.
2. **Booted** to a known state.
3. **Enumerated every radio.** Sub-GHz HaLow, conventional Wi-Fi, and LoRa. A
   missing radio is a failed gate, not a warning.
4. **Formed a mesh** with a known-good reference node.
5. **Served the access point**, with a client associating successfully.
6. **Passed a traffic smoke test** across each bearer.
7. **Survived a reboot**, returning to the same state without intervention.
8. **Demonstrated rollback** to the known-good path, per `FML-ADR-041`.

All eight. A candidate that fails any one is not promoted, and the failure is
recorded so the next candidate does not repeat it.

Steps 3 through 6 are why **a green CI pipeline is not a promotion**. CI has no
radios; see `test/README.md`. The gate is run on hardware, by a person, and its
evidence is recorded.

## Deployment freeze

**No promotion occurs during a deployment freeze, except by recorded
exception.**

A deployment freeze is declared when nodes are, or are about to be, in
operational use: an active incident, a scheduled exercise, or a training event
where a failure would matter. It is lifted explicitly.

An exception requires:

- A written statement of what is being promoted and why it cannot wait.
- Who authorised it, by name.
- What the rollback plan is, and who will execute it.
- A record in `CHANGELOG.md`.

An exception granted verbally and not recorded did not happen. The point of
recording is not bureaucracy: it is that the person who authorised a promotion
during an incident is the person who must be findable when it goes wrong.

## Signing

Image artifacts are signed. The signing key, its custody, and the verification
path on the node are **`TBD`** and interact with `TBR-SEC-01`.

Constraints that hold regardless of mechanism:

- The signing key is not in this repository, and not on a node. See
  `SECURITY.md`.
- A node verifies a signature before installing an image, not after.
- The rollback path's integrity does not depend on the active root's.

## Versioning

Two schemes, deliberately separate.

**Repository releases:** `v<MAJOR>.<MINOR>.<PATCH>`, as a git tag. Versions the
documentation, the build definitions, and the tooling. `ROADMAP.md` defines
`v0.0.1`.

**Image artifacts:** build date and content hash, in the form
`mule-<YYYYMMDD>-<short-hash>`. Not semantic versioning, because an image is
not an API and a semantic version implies a compatibility promise the program
cannot make across hardware blocks and region profiles.

An image artifact records, in its manifest:

- The compatibility set version from `os/kernel/PINS.md`.
- The repository commit it was built from.
- The hardware block it was built for.
- The region profile it was validated against.
- Its content hash.

A node reports these, which is what makes a field fault report actionable.

## Dependency updates

Automated update proposals are opened and **never auto-merged**. Promotion of a
dependency is a decision, per `FML-ADR-040`. See `renovate.json`.

## A/B update and rollback

The update scheme installs into an inactive slot and switches on next boot,
retaining the previous slot as the known-good path. `FML-ADR-041` decides the
**principle**; the **mechanism** is `TBR-REC-01`, and A/B slots are one
candidate among several rather than a decision.

Whatever the mechanism, rollback must work **without disassembly and without a
host computer**, by a volunteer, in the field, following a written procedure.

## SBOM

See `SBOM.md`.

## Release record

Each release records: set version, artifact hash, promotion gate evidence path
under `test/results/`, who promoted it, the date, and any freeze exception.

**No releases.**
