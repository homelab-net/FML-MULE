# Compatibility set pins

**Every version here is `TBD`.** Nothing has been selected, built, or tested.

These pins define the **compatibility set**: the kernel, out-of-tree radio
driver, radio firmware, and required userspace, which are versioned, tested and
promoted **together and never independently**. See `FML-ADR-040`.

**A change to any pin below creates a new candidate set** that must pass the
full promotion gate in `os/release/README.md`: rebuild all out-of-tree modules,
boot, enumerate every radio, form a mesh, serve the access point, pass a
traffic smoke test, survive a reboot, and demonstrate rollback.

Editing a pin without running the gate is the specific failure this file exists
to prevent.

## Set identity

| Field | Value |
| --- | --- |
| Set version | `TBD` |
| Date promoted | `TBD` |
| Promoted by | `TBD` |
| Status | `UNVERIFIED` - no set has ever been built |
| Region profile validated against | `TBD` |
| Hardware block | `TBD` - see `TBR-HW-01` |

## Kernel

| Field | Value | Source |
| --- | --- | --- |
| Tree | `TBD` | `TBR-LINUX-01` |
| Version | `TBD` | `TBR-LINUX-01` |
| Commit or tag | `TBD` | |
| Configuration | `TBD` | |
| Patch set applied | none | `os/kernel/patches/` is empty |
| Fork entry | not applicable | `docs/forks/` has no entries |

Whether this is a stock distribution kernel, a stock upstream kernel with
carried patches, or a vendor tree is the open question in `TBR-LINUX-01`.

## Out-of-tree radio driver

| Field | Value | Source |
| --- | --- | --- |
| Driver | `TBD` | `TBR-LINUX-01` |
| Version | `TBD` | |
| Upstream | `TBD` | |
| Commit or tag | `TBD` | |
| Build method | `TBD` - DKMS or in-image | `TBR-LINUX-01` |
| Kernel versions known to build | `TBD` | |

## Radio firmware

| Field | Value | Source |
| --- | --- | --- |
| Firmware | `TBD` | `TBR-LINUX-01`, `TBR-HW-01` |
| Version | `TBD` | |
| Source | `TBD` | |
| Driver versions it pairs with | `TBD` | |
| Redistribution terms | `TBD` | |

Firmware redistribution terms matter for a repository published for other
makers to build from. A firmware blob that cannot be redistributed changes how
the image build has to work.

## Required userspace

The tools that configure and operate the radios. Coupled to the driver, and
part of the set.

| Component | Version | Source |
| --- | --- | --- |
| `iw` | `TBD` | |
| `wpa_supplicant` | `TBD` | |
| `hostapd` | `TBD` | |
| `batctl` | `TBD` | |
| `batman-adv` | `TBD` | `FML-ADR-024` |
| Vendor configuration tooling | `TBD` | `TBR-LINUX-01` |

`batman-adv` appears here rather than under the kernel because it is versioned
and built alongside `batctl`, and the two must match.

## Package manifest

The userland package set is pinned separately in `os/image/manifest/`. That
manifest is part of the same compatibility set; it is kept in its own file
because it is long and machine-readable.

## History

No set has been promoted. When one is, record it here: set version, date, what
changed, and the promotion evidence path. A pin file with no history is a pin
file nobody can audit.
