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

| Reading | Real source | Units | Status |
| --- | --- | --- | --- |
| `temperatures_c` | `/sys/class/thermal/thermal_zone<N>/temp`, matched by the sibling `type` file | millidegrees C | `READER`. Zone-to-sensor map is per board and empty until `TBR-HW-01`. |
| `throttling_reported` | No portable interface. Raspberry Pi has `vcgencmd get_throttled`; others expose cooling-device state, vendor sysfs, or nothing. | flag | `NO SOURCE` until `TBR-HW-01`. Probe is injected; a platform with none reports `None`, never `False`. |

## Power

`mule/power.py`. No reader exists.

| Reading | Real source | Units | Status |
| --- | --- | --- | --- |
| `pack_present` | `/sys/class/power_supply/<supply>/present`, or the supply directory existing | flag | `NO READER`. Supply name is per board. |
| `pack_healthy` | `/sys/class/power_supply/<supply>/health`, a string such as `Good` or `Overheat` | enum string | `NO READER`. Mapping those strings to a boolean is a decision that belongs in `mule/power.py`, not in the reader. |
| `state_of_charge` | `/sys/class/power_supply/<supply>/capacity` | percent, 0-100 | `NO READER`. `mule/power.py` takes a fraction, so the reader divides. |
| `pack_temperature_c` | `/sys/class/power_supply/<supply>/temp` | **tenths of a degree C** | `NO READER`. Different unit from the thermal framework above. Reading it as millidegrees is a hundred-fold error that looks plausible. |

**Whether any of this exists at all depends on the battery assembly exposing a
power supply class device**, which needs a BMS with a kernel driver. CONOPS
section 59 requires a protected assembly; which one is `TBR-PWR-01` and
`TBR-HW-01`. A pack behind a bare I2C fuel gauge with no driver exposes none of
these, and `mule/power.py` already handles a pack that cannot report its charge.

## Time

`mule/timekeeping.py`. No reader exists.

| Reading | Real source | Units | Status |
| --- | --- | --- | --- |
| `rtc_present` | `/sys/class/rtc/rtc0/` exists, or `/dev/rtc0` | flag | `NO READER` |
| `rtc_backup_cell_ok` | **No standard interface.** The RTC class ABI defines no battery-low node. Some drivers expose a voltage-low flag; most do not. | flag | `NO SOURCE`. See the finding below. |
| `rtc_time` | `/sys/class/rtc/rtc0/time` and `date`, or `hwclock -r` | ISO date and time | `NO READER` |
| `system_time` | The running clock | timestamp | `NO READER`, and trivial: no kernel interface needed. |
| `synchronized` | `timedatectl show -p NTPSynchronized`, or chrony's own `chronyc tracking` | flag | `NO READER`. `FML-ADR-042` names chrony. |

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
