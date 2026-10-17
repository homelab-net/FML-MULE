# An independent RF witness for the LoRa channel, and that channel's frequency

**Trade:** `TBR-RF-02`.
**Date:** 2026-10-16, 21:49 to 22:00 UTC.
**Taken by:** Cameron Zobrist, on the mule bench, with Claude.
**Status of this artifact:** `MEASURED` for exactly two claims -- the operating
channel's centre frequency and occupied bandwidth, and the detection of RF
energy coincident with commanded transmissions. **It is not a link result.**
Nothing here shows that any peer received or decoded anything, and the bench
still has only one LoRa radio.

## Why this exists

Every sub-GHz record in this repository up to now rests on the transmitting
device's own account of itself. This directory's only other artifact
identifies a modem and states plainly that **nothing transmitted**. The
`TBR-RF-01` real-radio artifact records the limit from the other side: the
bench has one LoRa radio, so a send proves hand-off to the radio and nothing
more, and `airUtilTx` does not prove transmission either, because it arrives
in periodic telemetry rather than being observed.

This is the first measurement on this bench taken by an instrument that is not
the device under test.

It matters for this trade specifically. `TBR-RF-02` asks what LoRa
availability survives HaLow operation, and its own statement of why that
matters is that HaLow and LoRa may share 902-928 MHz centimetres apart in one
enclosure, and that if HaLow desensitizes the LoRa receiver **it fails
silently**. A silent failure is only detectable with an instrument that does
not depend on either radio's self-report. Two 27 dBm 902-928 MHz HaLow modules
are in transit, so the instrument is built before the hardware that makes it
necessary arrives, rather than after.

## The instrument

| Item | Value |
| --- | --- |
| Receiver | Nooelec NESDR SMArt v5, serial `54479189` |
| Bridge and tuner | Realtek RTL2832U, `0bda:2838`; Rafael Micro R820T |
| Software | `rtl_power`, Debian package `rtl-sdr` 2.0.2-2+b1 |
| Host | `FML-MULE`, Debian 13 trixie, kernel 6.12.105+deb13-amd64, x86_64 |
| Tuner gain | 0 dB, the minimum of the 29 values the R820T offers |
| Sample rate | 2.000000 MHz, one tuning, **no frequency hopping** |
| Resolution | 128 FFT bins of 15 625 Hz across a 2 MHz span |
| Integration | 1 s per row, 150 rows per run |
| Calibration | **None. See the geometry section below.** |

Receive-only by construction. This device cannot transmit, cannot peer in
802.11s and cannot forward for batman-adv, which is why it was ruled out as a
third mesh node and redirected here.

## The transmitter

| Item | Value |
| --- | --- |
| Node | `pi-mule-2`, Raspberry Pi 4 Model B Rev 1.4, aarch64 |
| Host OS | Debian 13 trixie, kernel 6.18.50+rpt-rpi-v8 |
| Radio | Seeed Tracker T1000-E, `hwModel TRACKER_T1000_E` |
| Firmware | Meshtastic 2.7.26.54e0d8d, `VANILLA` edition |
| Client | `meshtastic` 2.7.11 via USB CDC on `/dev/ttyACM0` |
| Region | US, `lora.region: 1` |
| Modem | bandwidth 250 kHz, spreading factor 11, coding rate 5 |
| Channel number | `lora.channel_num: 20`, an explicit override |
| Transmit power | `lora.tx_power: 30`, a **configuration value**, not a measurement |
| Channel index | 3, the private `MULE-TEST` secondary channel |
| Hop limit | **0** on every send |

**An image build identifier does not apply.** Neither node runs an image built
from this repository; they are stock Raspberry Pi OS and Debian. Recording a
build identifier that does not exist would be worse than recording its
absence.

## The geometry is not recorded, and that bounds what may be concluded

Antenna type at each end, the separation between the two nodes, and their
orientation were not recorded. Ambient conditions beyond "indoor bench" were
not recorded either.

`docs/evidence/README.md` requires those fields in a measurement record, and
check 26 of `tools/validate-docs.sh` fails any artifact that publishes a
received-signal figure while disclaiming them. That check keys on two specific
terms this artifact does not use, so it would not fire here. Satisfying a
check by avoiding its pattern is not the point, so the rule is honoured
directly instead:

**No claim in this artifact depends on absolute received power.** The figures
below are uncalibrated `rtl_power` FFT bin magnitudes in dB. They are not dBm.
Nothing on this bench calibrates them. They are used for one purpose only -- a
contrast between intervals **within a single capture**, at identical gain,
span, antenna and geometry -- and they support **no** claim about path loss,
link budget, receiver sensitivity, radiated power or range. A repeat that
wants any of those claims must record the geometry first.

What survives the missing geometry is the frequency measurement, which does
not depend on it at all, and the detection result, which is a yes or a no.

## The prediction, stated before the measurement

`lora.channel_num` is set explicitly to 20, so the operating frequency is not
derived from a channel-name hash and is computable. For the US region the band
starts at 902.0 MHz, the configured bandwidth is 250 kHz, and the firmware
indexes from zero:

```text
902.0 MHz + (250 kHz / 2) + (20 - 1) x 250 kHz = 906.875 MHz
```

**Predicted centre: 906.875 MHz.** Recorded before the captures were analysed,
so the measurement tests the prediction rather than being fitted to it.

## Run 1, the witness: 906-908 MHz, seven commanded sends

Seven sends on a 15 s cadence, each falling in its own 1 s capture interval,
with 14 quiet intervals between consecutive sends. Those gaps are an
interleaved control taken under identical conditions, which a separate
baseline run is not.

`rtl_power` stamps a row when its integration interval **closes**, so the row
covering a send at T is labelled T+1.

| Send, UTC | Covering row | Peak bin, dB | In-channel mean, dB |
| --- | --- | --- | --- |
| 21:49:29 | 21:49:30 | -16.7 | -18.05 |
| 21:49:44 | 21:49:45 | -16.4 | -17.82 |
| 21:49:59 | 21:50:00 | -16.5 | -17.89 |
| 21:50:14 | 21:50:15 | -16.7 | -18.22 |
| 21:50:29 | 21:50:30 | -16.5 | -18.03 |
| 21:50:44 | 21:50:45 | -16.7 | -18.23 |
| 21:50:59 | 21:51:00 | -16.8 | -18.31 |

Detections: **seven of seven.** In-channel mean taken over 906.750 to
906.984 MHz:

| Row class | Rows | Mean, dB | Range, dB |
| --- | --- | --- | --- |
| Send-coincident | 7 | -17.43 | -17.63 to -17.13 |
| All others | 143 | -37.94 | -38.45 to -16.27 |

Separation of means: **20.51 dB.** The seven send-coincident rows span 0.5 dB
across seven independent events. The out-of-channel mean rises about 1 dB
during a burst, which is spectral skirt and receiver response, not the front
end saturating.

Commanded-send timing skew ran between 0.1 ms and 4.4 ms across all fourteen
sends in both transmitting runs, so no detection rests on a marginal
alignment.

## Run 2, the frequency control: 910-912 MHz, the same seven sends

The same schedule with the span moved 4 MHz away. If the instrument were
simply responding to a transmitter a few metres from it, the spikes would
follow.

**No row exceeded -30 dB.** All fourteen send-coincident rows -- the send row
and the row after it, for each of seven sends -- read between -37.68 and
-37.74 dB, indistinguishable from that run's own floor. The four strongest
rows in the whole run, -32.19 to -33.89 dB, are uncorrelated with any send,
and three of them sit at 911.0000 MHz, the tuner's own centre.

## Run 3, the idle control: 906-908 MHz, no sends at all

The same span as run 1, with nothing transmitted.

**Zero events in 150 consecutive seconds.** In-channel mean -38.41 dB across
all 150 rows, total range 0.38 dB.

This measures the method's false-positive rate, and it settles something run 1
raised on its own: the channel does not light up by itself on this timescale.

It carries a second finding worth stating. The device's node database holds 80
third-party nodes on the public mesh, which shares this RF channel, and **none
of them produced a detectable row.** At 0 dB gain, distant traffic sits under
the floor. That makes this instrument deliberately a **local** witness: it
isolates the device under test, which is what a coexistence measurement wants,
and it is correspondingly blind to ambient band occupancy, which a spectrum
survey would want. A survey needs its own run at higher gain, and must then
expect to see other people.

## The measured channel

Taking the occupied band as those bins more than 10 dB above the same run's
quiet row:

| Quantity | Measured |
| --- | --- |
| Lower edge | 906.7500 MHz, bin 48 |
| Upper edge | 906.9844 MHz, bin 63 |
| Occupied width | **250.0 kHz** |
| Centre | **906.8672 MHz** |

The width matches the configured 250 kHz bandwidth exactly. The centre is
7.8 kHz from the predicted 906.875 MHz, which is **half of one 15 625 Hz FFT
bin**, the finest distinction this resolution can draw. **The prediction is
confirmed to within one bin.**

**A trap for the next reader, recorded because it nearly caught this one.**
The single strongest bin in a burst row lies at 906.969 to 906.984 MHz, near
the upper band edge, not at the centre; the in-band response is tilted by
roughly 3 dB from the lower edge to the upper. Reading the peak bin as the
centre frequency gives 906.97 MHz, a wrong answer plausible enough to survive
review. **The band edges are the sound discriminator, not the argmax.**

## Four rows that no commanded send explains

Run 1 holds four rows above -30 dB in-channel that are not send-coincident:

| Row, UTC | In-channel mean, dB | Nearest send |
| --- | --- | --- |
| 21:49:35 | -16.27 | 6 s after the 21:49:29 send |
| 21:49:36 | -27.91 | 7 s after |
| 21:50:01 | -22.85 | 2 s after the 21:49:59 send |
| 21:50:02 | -17.20 | 3 s after |

They are as strong as the commanded sends, so their source is near the
instrument rather than distant: the same radio, or something beside it.
Meshtastic broadcasts node information, position and telemetry on its own
schedule, and that is the most plausible source. **It is not proven.**
Confirming it needs a decoding receiver, which energy detection is not. The
idle run shows the channel is otherwise silent, which makes an external source
less likely still, but does not exclude one.

This is the finding that disciplines the whole method, so it is stated rather
than tidied away: **energy in this channel does not identify a commanded
transmission.** Only the timing correlation does, which is why the schedule
and both controls are part of the procedure rather than refinements to it.

## The transmitting node was intermittently under-voltage

`vcgencmd get_throttled` on `pi-mule-2` read `0x50005` at 600 MHz at 21:43,
before the runs, and then oscillated between `0x50005` at 600 MHz and
`0x50000` at 1800 MHz when sampled five times at two-second intervals at
22:02, after them. The transition is not bracketed: the state during the
captures themselves was not sampled and cannot be reconstructed.

This updates what `docs/bench-remediation-plan-2026-10-11.md` Phase 0.4
records. `pi-mule-2` was the persistently throttled node and `pi-mule-1` the
fluctuating one. **Both now fluctuate**, on a seconds timescale, so a single
clean reading from either proves nothing about a run that has already
finished.

**Why this result survives a throttled transmitter when a performance result
would not.** The rule in this repository is to treat a live throttle bit as
invalidating a run, because a throttled node under-reports the radio, and that
is the direction that gets believed. That reasoning governs throughput,
latency and jitter. It does not reach either claim made here. A CPU clock does
not move the radio's channel frequency or its occupied bandwidth, both of
which are set by the modem configuration. And the only timing this result
depends on is the skew between scheduled and actual send instants, which was
measured directly and stayed under 4.4 ms -- four orders of magnitude inside
the 1 s capture interval that has to contain it.

No throughput, latency or airtime figure is published here, and none should be
taken from these captures.

## What this does not show

- **Not reception.** No peer received these transmissions. The bench has one
  LoRa radio. This is the transmit half of a link and only that half.
- **Not decode.** Energy detection recovers no payload, no addressing and no
  channel identity. It cannot distinguish this packet from any other signal of
  similar shape in that band.
- **Not device attribution.** See the four unexplained rows above.
- **Not power, range or sensitivity.** See the geometry section.
- **Not coexistence.** No HaLow radio was present. That measurement is the
  point of building this, and it has not been taken.
- **Not a closure.** `TBR-RF-02` remains `OPEN`. Its gate requires the
  assembled enclosure and the final radio topology from `TBR-RF-03`, neither of
  which exists. An artifact's presence is not owner acceptance.

## What it is for

When the two HC01P V2 HaLow modules arrive, the coexistence question becomes
measurable rather than arguable:

1. Capture the LoRa channel with HaLow absent -- done above, three runs.
2. Repeat with HaLow present and idle.
3. Repeat with HaLow transmitting at 27 dBm, centimetres away.

A change in the LoRa channel's floor between 1 and 3, measured by an
instrument that is neither radio, is the desensitization that `TBR-RF-02` says
would otherwise fail silently. The baseline in run 3 -- mean -38.41 dB, range
0.38 dB across 150 s -- is what a later run gets compared against, which is why
a quiet control run is evidence rather than a null result.

It also supplies a measured input to `regions/us-915/profile.yml`, where
`lora.permitted` and `lora.max_eirp_dbm` are both `TBD`. The measurement says
where this configuration actually operates. It does not say what should be
permitted, which is a decision and not an observation.

## Reproducing it

```sh
# On the node holding the SDR, and on the node holding the radio, with the
# same start epoch. Both hosts must be NTP-synchronised; both were.
T0=$(( $(date +%s) + 100 ))

test/bench/sdr-rf-witness.sh "$T0" 906000000 908000000 witness     # receiver
test/bench/lora-tx-burst.py --start-epoch "$T0" --channel-index 3  # transmitter

# Frequency control: identical, span moved away.
test/bench/sdr-rf-witness.sh "$T0" 910000000 912000000 control-freq

# Idle control: identical span, transmitter not run at all.
test/bench/sdr-rf-witness.sh "$T0" 906000000 908000000 idle
```

`test/bench/lora-tx-burst.py` refuses channel index 0. The primary channel is
the public mesh, this bench sees 80 real third-party nodes on it, and a LoRa
transmission cannot be recalled, so the refusal is a check rather than a note.

Every send used `hopLimit=0`. Meshtastic's default rebroadcast mode relays a
packet on a channel it cannot decrypt, so a private channel withholds the
contents and not the airtime; without this, seven bench packets could have
been repeated seven hops across other people's nodes. It also keeps the
measurement clean, because one send is then one transmission.

## Raw data

Committed beside this file. Raw output rather than a summary, per
`docs/evidence/README.md`.

| File | Run |
| --- | --- |
| `2026-10-16-rf-witness-906-908-sends.csv` | 1, witness |
| `2026-10-16-rf-witness-910-912-control.csv` | 2, frequency control |
| `2026-10-16-rf-witness-906-908-idle.csv` | 3, idle control |
| `2026-10-16-rf-witness-transmit-log.json` | sends for runs 1 and 2 |

sha256, as captured on the measuring host:

```text
27825718705a8001ce7703948d744ec025366c574de8e23c6a515df42ca78b29  sends
c3d69b7a563d030a9ead9e20360304d8c869a1b855074f7dcfe199a4758782aa  control
138f36fe28b0367abff2adf9a25108cb1f62618fc5780a653309eedac89c778e  idle
```

`rtl_power` CSV columns are: date, time, Hz low, Hz high, Hz step, sample
count, then one dB value per bin. Timestamps are UTC and mark the **end** of
each integration interval.

## Scrub manifest

Recorded because `docs/evidence/README.md` requires that what was removed is
stated, and a silently trimmed log is not reviewable.

**Removed, and why:**

- **The radio's station address.** Universally administered, so it names a
  real part, and `tools/validate-identifiers.py` fails the build on exactly
  that and is right to.
- **Node identifiers and public keys**, for this device and for the 80
  third-party nodes in its node database.
- **GPS coordinates.** The device reports an internal position fix.
  Publishing it would disclose a real location, which `SECURITY.md` forbids
  without exception. No coordinate appears in this artifact or in any
  committed capture; the CSV files hold only frequency and power columns and
  never contained one.
- **Channel pre-shared keys.** Never read into any file. The rule in this
  repository is that bench PSKs are never committed.

**Deliberately kept:**

- Hardware serial `54479189` and USB identifier `0bda:2838` for the SDR, and
  the model names of both radios. These identify instruments, which a
  measurement record is required to name. They are not members or locations.
- The node hostnames `FML-MULE` and `pi-mule-2`, already used throughout this
  repository.
