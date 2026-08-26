# Operating system

This is where the program's first functional code lives. **Build system before
application code**: the image build and configuration pipeline comes before
features, because features need something to install onto.

## The two-layer split

This governs almost every decision in this directory, and it is the single most
important idea to understand before changing anything here.

**Layer one: the Debian-family userland.** Portable. Expected to move between
compute modules with configuration changes only. Package manifests, services,
network configuration, provisioning. Decided by `FML-ADR-022`. A contributor
can reproduce most of it on an ordinary laptop.

**Layer two: the kernel and board support package.** Hardware-specific, and
**may require vendor patches**. Kernel, device tree, out-of-tree radio driver,
radio firmware, bootloader. Not portable, and not reproducible without the
hardware.

The split is drawn deliberately at this line so that the program can carry a
vendor kernel beneath a portable userland if it has to. Whether it has to is
`TBR-LINUX-01`, and it is the trade the whole of this directory waits on.

If a kernel patch set turns out to be required, the program acquires a
**maintained fork**: a named owner, a rebase cadence, an upstream submission
posture, and an entry in `docs/forks/`. That is a permanent liability attached
to a specific person. `tools/validate-docs.sh` fails the build if a patch file
exists in `os/kernel/patches/` with no fork entry, because the alternative
failure is silent.

## One tested compatibility set

**The kernel, out-of-tree radio driver, radio firmware, and required userspace
are promoted as one tested compatibility set. Never independently.**
`FML-ADR-040`.

Out-of-tree modules are coupled to a kernel version, radio firmware is coupled
to a driver version, and the userspace that configures the radio is coupled to
both. Updating any one alone is how a fleet of nodes stops enumerating its
radios in the field, all at once, remotely, with no operator present.

Consequences you will meet in this directory:

- A change to any pin creates a **new candidate set**, which must pass the full
  promotion gate in `os/release/README.md`.
- Dependency update proposals are opened and **never auto-merged**. Promotion
  is a decision.
- A green CI run is not evidence the set works. **CI has no radios.** See
  `test/README.md`.
- A security update to one component cannot ship without re-qualifying the set.
  That is a real cost during an active vulnerability, and the program has no
  exception process for it yet. The gap is acknowledged in `FML-ADR-040` rather
  than hidden.

## Directory map

| Directory | Contents |
| --- | --- |
| `image/` | Image build definition and pinned package manifests. |
| `kernel/` | Kernel pin, patch set, out-of-tree driver build. `PINS.md` holds the set's versions. |
| `overlays/` | Device tree overlays. |
| `ansible/` | Host provisioning roles. |
| `config/` | Network, radio, firewall, DNS and DHCP templates. |
| `release/` | Release process, signing, A/B update scheme, SBOM. |

## Configuration is generated, not written

No file in `os/config/` contains a frequency, a channel, a bandwidth, or a
transmit power. Those come from a **region profile** in `regions/<region-id>/`.
Region is an input to configuration generation, never a constant. A repository
hardcoded to 902-928 MHz is unusable in the EU and UK. See `regions/README.md`
and `REGULATORY.md`.

The templates in `os/config/` are commented skeletons with `TBD` values and the
trade that will supply each one. They are deliberately not fillable-in-place
files; they are the input to generation.

## Poor connectivity is the normal case

Builders will be on constrained connections, and some will be building in the
field for the same reason the equipment exists. **Prefer vendored or cached
dependencies where practical.** A build that requires a fast connection to a
dozen upstream hosts is a build that fails where it matters.

This has consequences for how the image build is structured: prefer a local
package cache, prefer a single pinned manifest over resolution at build time,
and make it possible to build twice without downloading twice. The mechanism is
`TBD`; the preference is not.

## Current state

Nothing here builds yet. There is no image, no kernel pin, no provisioning that
has been run against real hardware, and no promotion has ever been performed.
Every version in `os/kernel/PINS.md` is `TBD`.

The first real work in this repository is here, and it starts when
`TBR-LINUX-01` has candidate hardware to run against.
