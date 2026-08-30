# What the node measures, and how

Every value the node reads from its own hardware, where that value really comes
from on a Debian-family node (`FML-ADR-022`), and whether code exists to read it.

**Why this file exists.** `mule/thermal.py` was written with a complete decision
and no way to obtain the readings it judged. Nobody noticed until someone asked
how thermal would actually read on the selected hardware, and that question
immediately found a defect: an interface that could not express "this platform
cannot tell me". A decision written without knowing what the platform can
actually provide will get the shape of its inputs wrong.

So the question is asked here, in advance, for every reading.
`tools/validate-docs.sh` fails if a reading method in `mule/` has no row.

## Kernel interface, or a command?

Every reading is one of three kinds, and the difference is not cosmetic.

| Kind | What it costs |
| --- | --- |
| `kernel` | Nothing. `sysfs` and `procfs` are kernel ABI: stable across distributions and releases, present on every Debian-family node without installing anything. |
| `command` | A package in the image, a fork and exec per reading, and a parsing surface. Command output is **not** ABI-stable the way `sysfs` is; a version bump can reword it. |
| `none` | No interface exists at all, on any platform. |

**Prefer a `kernel` source to a `command` every time one exists.** A reading
that shells out has quietly created a dependency on the image containing that
binary, and if `os/image/manifest/packages.list` does not carry it, the reading
fails in the field on a node nobody can reach. `vcgencmd` is the sharpest case:
it is Raspberry Pi VideoCore userland, not a Debian package at all, so a reading
that needs it constrains `TBR-HW-01`.

Every `command` row names the package that provides it, so the image build has
something to guarantee. `tools/validate-docs.sh` requires that, and reports how
many of those packages are actually pinned. Today none are, because nothing is
pinned at all: the manifest is empty pending `TBR-LINUX-01`.

## How to read the status column

| Status | Meaning |
| --- | --- |
| `READER` | Production code exists and is exercised. Says nothing about whether it works on any board; see the note at the bottom. |
| `NO READER` | The interface is decided and nothing implements it yet. |
| `NO SOURCE` | No standard interface exists, or the hardware that would provide it is unselected. Named trade says what would change that. |

Units are recorded because they differ between kernel subsystems in ways that
produce silent hundred-fold errors. The thermal framework reports
**millidegrees**; the power supply class reports **tenths of a degree**.

## Thermal

`mule/thermal.py`, read by `mule/sysfs.py`.

| Reading | Kind | Real source | Units | Status |
| --- | --- | --- | --- | --- |
| `temperatures_c` | `kernel` | `/sys/class/thermal/thermal_zone<N>/temp`, matched by the sibling `type` file | millidegrees C | `READER`. Zone-to-sensor map is per board and empty until `TBR-HW-01`. |
| `throttling_reported` | `none` | No portable interface. Raspberry Pi has `vcgencmd get_throttled`, which needs package `libraspberrypi-bin` and is not Debian-general; others expose cooling-device state, vendor sysfs, or nothing. | flag | `NO SOURCE` until `TBR-HW-01`. Probe is injected; a platform with none reports `None`, never `False`. |

## Power

`mule/power.py`. No reader exists.

| Reading | Kind | Real source | Units | Status |
| --- | --- | --- | --- | --- |
| `pack_present` | `kernel` | `/sys/class/power_supply/<supply>/present`, or the supply directory existing | flag | `NO READER`. Supply name is per board. |
| `pack_healthy` | `kernel` | `/sys/class/power_supply/<supply>/health`, a string such as `Good` or `Overheat` | enum string | `NO READER`. Mapping those strings to a boolean is a decision that belongs in `mule/power.py`, not in the reader. |
| `state_of_charge_fraction` | `kernel` | `/sys/class/power_supply/<supply>/capacity` | percent, 0-100 | `NO READER`. The method returns a **fraction**, so the reader divides; the unit is in its name so that step cannot be forgotten. |
| `pack_temperature_c` | `kernel` | `/sys/class/power_supply/<supply>/temp` | **tenths of a degree C** | `NO READER`. Different unit from the thermal framework above. Reading it as millidegrees is a hundred-fold error that looks plausible. |

**Whether any of this exists at all depends on the battery assembly exposing a
power supply class device**, which needs a BMS with a kernel driver. CONOPS
section 59 requires a protected assembly; which one is `TBR-PWR-01` and
`TBR-HW-01`. A pack behind a bare I2C fuel gauge with no driver exposes none of
these, and `mule/power.py` already handles a pack that cannot report its charge.

## Mesh state

`mule/bringup.py`, the `MeshState` dataclass read by `state_violations`. No
reader exists.

**`tools/validate-docs.sh` did not require these rows and that is a gap, not a
permission.** `tools/list-readings.py` walks Protocol classes under `mule/`;
`MeshState` is a dataclass, so the check never saw it and four readings were
added with no statement of where they come from. That is the `mule/thermal.py`
failure this file exists to prevent, repeated in a different shape.

| Reading | Kind | Real source | Units | Status |
| --- | --- | --- | --- | --- |
| `routing_algo` | `command` | `batctl routing_algo`, package `batctl`. **Not `sysfs`.** batman-adv removed its `sysfs` interface; on kernel 6.12.105+deb13-amd64 a `batadv` device has no `mesh/` directory at all, so the value is only reachable over netlink and `batctl` is what speaks it. | name | `NO READER` |
| `bridge_loop_avoidance` | `command` | `batctl bridge_loop_avoidance`, package `batctl`. Same reason. | flag | `NO READER` |
| `hard_mtu_bytes` | `kernel` | `/sys/class/net/<iface>/mtu`. The one here that is a plain kernel read, because it is an ordinary link attribute rather than a batman-adv one. | bytes | `NO READER` |
| `mesh_member_count` | `command` | `batctl interface`, package `batctl`. Netlink again. | count | `NO READER` |

**Three of the four need `batctl` in the image**, which
`os/image/manifest/packages.list` has to guarantee, and `os/kernel/PINS.md`
already requires `batctl` and the module to match under `FML-ADR-040`. A
reading that shells out has created a dependency on the image carrying that
binary, and if it does not, the reading fails in the field on a node nobody can
reach.

**The removal of batman-adv `sysfs` is the finding worth carrying.** Any design
that assumed these values could be read the way thermal zones are read is
wrong on a current kernel.

## LoRa plane

`test/flatsat/interfaces.py`, the `LoRaPlane` Protocol. It is in `test/` rather
than `mule/` because `FML-ADR-052` keeps an interface whose shape an open trade
governs out of the production package, and addressing on this plane is
`TBR-NET-02`. `tools/validate-docs.sh` therefore does not require this row; it
is here because the question it asks -- where does this really come from on a
Debian node, and what happens when the platform cannot answer -- is worth
answering before the interface exists rather than after.

| Reading | Kind | Real source | Units | Status |
| --- | --- | --- | --- | --- |
| `stack_responding` | `command` | Meshtastic exposes no kernel interface: the radio attaches over USB serial, UART or TCP (`FML-ADR-026`) and the stack is a userspace daemon. The reading is whether that daemon answers its API. Package is whatever `FML-ADR-048` settles on and **is not selected**; `meshtasticd` is what `.github/workflows/lora-probe.yml` runs. | flag | `NO READER`. Probe only. |

**Why this is not a `kernel` reading, and why that costs something.** Every
other row here can be answered from `sysfs`. This one cannot: there is no
kernel object for "is the LoRa stack carrying". The node has to ask a userspace
daemon, which means a package in the image, a process that can exit, and an
answer that is not ABI-stable. `.github/workflows/lora-probe.yml` found the
daemon exits when its configuration changes, so this is not a theoretical
failure mode.

**Why the type is `bool | None`.** A socket that neither answers nor refuses,
or a node with no API endpoint configured, leaves the platform unable to tell.
That is a third state and not a polite "no". `mule/status.py` reads `None` as
not available, which is the fail-closed direction on the bearer CONOPS section
50.8 leaves an operator when everything else has gone.

## Time

`mule/timekeeping.py`. No reader exists.

| Reading | Kind | Real source | Units | Status |
| --- | --- | --- | --- | --- |
| `rtc_present` | `kernel` | `/sys/class/rtc/rtc0/` exists, or `/dev/rtc0` | flag | `READER`. `mule/sysfs.py`, run against a real `rtc_cmos` device. |
| `rtc_backup_cell_ok` | `none` | **No standard interface.** The RTC class ABI defines no battery-low node. Some drivers expose a voltage-low flag; most do not. | flag | `NO SOURCE`. See the finding below. |
| `rtc_time` | `kernel` | `/sys/class/rtc/rtc0/since_epoch`, one read rather than parsing `date` and `time` separately: no locale, and no midnight race between two files. Package `util-linux` provides `hwclock -r`, which is **not** needed. | seconds since epoch | `READER`. `mule/sysfs.py`. |
| `system_time` | `kernel` | The running clock, through the standard library | timestamp | `READER`. `mule/sysfs.py`. |
| `synchronized` | `command` | `chronyc tracking`, package `chrony`. `FML-ADR-042` names chrony as the daemon, so the package is required regardless and the dependency costs nothing extra. Package `systemd` would provide `timedatectl show -p NTPSynchronized` as an alternative. | flag | `NO READER` |

### Finding: the flagship fail-closed case may have no signal

`FakeClock.dead_backup_cell()` is the scenario `FML-ADR-042` was written for,
and the one the flat-sat exercises hardest. It depends on
`rtc_backup_cell_ok`, and **the Linux RTC class defines no standard way to ask.**

Consequences worth deciding rather than discovering:

- On a board whose RTC driver exposes nothing, that reading is permanently
  `None`, and `mule/timekeeping.py` already treats `None` as "not by itself a
  refusal" and falls through to its plausibility checks. So the node still
  fails closed on a depleted cell, but by noticing the **time is implausible**
  rather than by being told the cell is flat.
- That is a weaker and slower signal. A cell that has just failed, on a node
  that has not yet drifted, looks fine.
- Whether the selected RTC exposes a battery-low flag is therefore a **selection
  criterion**, not an implementation detail. It belongs in `TBR-TIME-01` and
  `TBR-HW-01`.

## What a `READER` status does and does not mean

It means production code exists and its tests pass against a **synthetic**
interface built to the documented ABI. It means nothing about any board.

No reading in this table has been taken from real hardware. A capture from a
real node belongs in `test/fixtures/`, with the node identifier, capture date
and image build recorded alongside it, per `docs/evidence/README.md`. Until then
every row here describes an interface, not a measurement.
