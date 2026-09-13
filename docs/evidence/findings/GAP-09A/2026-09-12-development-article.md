# Development compute article selection

**Date:** 2026-09-12. **Purpose:** GAP-09A and the `v0.0.1` vertical slice.
**Selection:** the existing Intel N150 lab system is the development compute
article. **Authority:** Program Owner approval in the Codex thread on
2026-09-12.

This selection means the project may use hardware it already possesses to build
and exercise the portable Debian service path. It is not the production compute
selection in `TBR-HW-01`, does not qualify a hardware block, and does not promote
the kernel, drivers, or userspace as a field compatibility set under
`FML-ADR-040`.

## Sanitized inventory

Read-only inspection of the installed operating system reported:

| Property | Observation |
| --- | --- |
| Architecture | x86-64 |
| Processor | Intel N150, four logical CPUs |
| Operating system | Debian GNU/Linux 13.6 (trixie) |
| Kernel | Debian `6.12.105+deb13-amd64` |
| Memory | approximately 15 GiB usable RAM |
| Storage | approximately 477 GB block storage |

The inventory came from `/etc/os-release`, `uname`, `lscpu`, `free`, and
`lsblk`. Network identifiers, addresses, interface hardware identifiers,
credentials, serial numbers, and deployment location are deliberately omitted.
These observations establish what the development article is; they are not a
resource threshold or functional benchmark.

## Compared alternatives

| Option | Fit for this milestone | Disposition |
| --- | --- | --- |
| Existing Intel N150 lab system | Available now, already runs the selected Debian family, and exercises the portable x86-64 userland path | Selected for development only |
| CM4 planning direction | Relevant to existing hardware and footprint trades, but production selection and qualification remain open | Retained for later trade evidence, not selected here |
| OpenMANET-supported boards | Useful comparative image, package, and radio-configuration prior art; its OpenWrt image is not the Debian host selected by `FML-ADR-022` | Reference only under `FML-ADR-023` |

Using the existing article is the smallest reversible step: no procurement and
no physical or software mutation is required to designate it. A different
development article can supersede this record without changing a production
architecture decision.

## Consequences

- GAP-09B may target a bootable Debian 13 x86-64 development image while
  keeping architecture-specific inputs explicit.
- Measurements on this system may establish only the development software path;
  they do not supply CM4, RF, power, thermal, or production capacity evidence.
- GAP-09I still requires an independent cold-start operator and repository-only
  rebuild. The existence of a working hand-configured lab stack does not satisfy
  that acceptance.
