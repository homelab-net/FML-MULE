# Bench

Bench procedures and instrumentation notes: how a measurement is taken, with
what, and what makes it repeatable.

**Six procedures. No measurement has been taken.**

`80211s-mesh.sh` exercises 802.11s association and batman-adv over it using
`mac80211_hwsim`, with no radio. It is a procedure rather than a measurement:
it asserts that the stack composes and that a mesh point reports carrier only
once joined, which `FML-ADR-059` depends on. It produces no number.

`--line` builds three nodes where node 1 cannot hear node 3, so reaching it
requires node 2 to relay. **That is multi-hop over real 802.11s**, which
nothing else here demonstrates: `.github/workflows/mesh-probe.yml` proves
multi-hop over `veth`, which is not wireless.

The line is made by channel separation rather than by `wmediumd`, which Debian
does not package. Node 2 carries a radio on each segment with both in one
`batman-adv` interface, which is not a trick to make a test pass: a node with
several bearers joined into one mesh is what `FML-ADR-045` describes and what
`os/config/networkd.conf.template` configures.

It does not run in CI and cannot: a hosted runner's kernel has no wireless
stack at all. Run it on a development machine, as root. See
`docs/dev-machine.md`.

`wan-gateway-sharing.sh` exercises `batman-adv` gateway mode over
`mac80211_hwsim`: two gateway-holding nodes and one WAN-less node. It records the
routing-logic half of `TBR-NET-04` -- a client selecting a gateway (through the
DHCP the gateway mode steers, not a route set by hand), reaching a server that
lives only behind that gateway's uplink, failing over to the surviving uplink,
and losing only WAN across an induced partition. It selects no
pooling-vs-failover answer and measures no throughput: `hwsim` has no RF, so
which gateway its equal-TQ tie-break picks is not a real-radio result, and
`FML-ADR-069`'s mechanism stays open. It needs `dnsmasq`, `iptables` and
`busybox` as well as `iw` and `batctl`, and like the others it does not run in
CI.

`map-server-mesh.sh` is the map analog of the gateway bench. A storage node
serves its `z/x/y` tile store over the mesh; a storage-less node fetches a tile
across `batman-adv` and it is byte-identical to the store's copy -- the
map-server-for-the-mesh role `services/map/README.md` names, which is the
`TBR-NET-04` share-a-resource pattern applied to `TBR-MAP-01`
(`docs/evidence/TBR-MAP-01/2026-09-05-map-server-over-mesh-hwsim.md`). It builds
its own store from a raw-PNG encoder, so no imagery is committed, and it selects
its two radios from the `mac80211_hwsim` device tree under `/sys` rather than by
name -- selecting mesh radios by a name or mode match once moved a live radio on
this bench host, and the driver-tree selector by construction cannot name a real
phy. It measures no serve rate: `hwsim` has no medium.

`keyed-mesh.sh` proves that a keyed 802.11s mesh admits only credential
holders, which is what `FML-ADR-061` decides and what `FML-ADR-060` was
superseded for getting wrong. It needs `wpasupplicant` as well as `iw`.

**It exists because the decision came first.** `FML-ADR-061` supersedes another
ADR on the strength of a measurement that, until 2026-08-31, lived only in a
scratch directory: nothing in the repository could reproduce it. A decision
resting on an unreproducible measurement is a decision resting on somebody's
word.

Its assertions read `mesh plink`, `authenticated` and `authorized`, never a
count of peers, because **`iw station dump` lists peers the radio has merely
seen**. A node that failed authentication still appears, in state `LISTEN`.
Counting those lines reports success for a node that got nowhere, and that
mistake was made while producing `FML-ADR-061` and caught only by reading the
flags. The generated credentials are per-run and nothing is committed.

`route-isolation.sh` reproduces the external-network failure and measures the
four candidate mechanisms `TBR-NET-01` has to choose between. It selects
nothing: its useful output is the table, not the exit code. It exists because
`FML-ADR-060` was superseded one day after it was written for deciding
something untested, and the next decision was `TBR-NET-01`'s.

`tak-state.sh` reproduces the two `TBR-TAK-01` findings a decision now rests
on: that OpenTAKServer is three processes and upstream's container runs one, and
that a database-only restore restores every row and authenticates nobody while
reporting healthy. `FML-ADR-034` makes PostgreSQL conditional on that state
study, so the measurement has to be reproducible by somebody other than its
author. It needs Podman and pulls three images, so like the others it does not
run in CI.

## What can be verified without hardware, and what cannot

Asked directly on 2026-08-31, and worth answering once rather than rediscovering.

**Already done in this program, with no radio:**

| Question | How |
| --- | --- |
| 802.11s association, and carrier only once joined | `80211s-mesh.sh`, `mac80211_hwsim` |
| Multi-hop over real 802.11s | `80211s-mesh.sh --line`, channel separation |
| `batman-adv` routing, `BATMAN_IV`, bring-up order, bridge loop avoidance | bench and `mesh-probe.yml` |
| **Keyed mesh: SAE + AMPE, and exclusion of non-holders** | `hwsim` + `wpa_supplicant`, `FML-ADR-061` |
| Addressing collision, distinct prefixes, routed liaison | `hwsim`, `docs/evidence/TBR-NET-01/`, `TBR-NET-03/` |
| An external route stealing part of the mesh | `veth`, `docs/evidence/TBR-NET-01/` |
| Meshtastic payload limits and tag survival | two `meshtasticd` instances |
| A fresh Debian install building the toolchain | CI job |

That is a larger set than it looks, and it covers most of the **protocol and
configuration** questions this program has asked.

**Two hard limits, both measured rather than assumed:**

**`hwsim` has no medium.** No path loss, no interference, no rate adaptation, no
distance. Every link is a perfect wire, so nothing about range, throughput,
capacity or partition-under-load can come from it.

**`hwsim` has no S1G band.** Checked on this kernel: `iw phy` reports Band 1 and
Band 2 only, 2.4 and 5 GHz. HaLow's 1, 2, 4, 8 and 16 MHz channels are not
available, so **mesh at 1 MHz cannot be simulated** -- and `FML-ADR-062` names
that as the material untested configuration, because HaLow's range argument
depends on it.

Worth knowing separately: **the S1G core is already in the kernel Debian ships**.
`mac80211.ko` carries 53 `s1g` symbols and `cfg80211.ko` 30, so a HaLow driver
does not need a patched kernel for S1G itself. It is `hwsim` that does not
expose the band, not the stack that lacks support.

**Two things would extend the reach, at real cost:**

- **`wmediumd`** gives `hwsim` a medium: per-link path loss and packet loss,
  which buys partition and heal, mobility, asymmetric links, and the
  per-direction `TQ` questions deferred in
  `docs/evidence/TBR-LINUX-01/2026-08-31-originator-count-differs-by-interface-order.md`.
  It is the more useful of the two and it is **not a `git clone` away.**

  **It has no canonical maintained upstream**, checked 2026-08-31. Debian does
  not package it. `bcopeland/wmediumd`, the upstream everything descends from,
  was last pushed 2021-03-02; `cozybit/wmediumd`, the origin, in 2013. The live
  activity is split between `ramonfontes/wmediumd`, one maintainer's fork
  oriented to Mininet-WiFi and last pushed 2026-07-23, and Android platform
  mirrors of `external/wmediumd` carried by several vendors.

  So adopting it means **selecting a fork and pinning it**, which under
  `FML-ADR-058` is a decision rather than a build step: that ADR pins every
  tool this repository installs, and adding an unpinned build from somebody's
  fork would be inconsistent with it. An earlier version of this section said
  the tool "is carried actively as `external/wmediumd` in AOSP", which
  overstated a split and unowned situation.
- **An `hwsim` S1G band** would be a kernel patch. The core support exists, so
  the work is exposing a band rather than implementing S1G. Bounded, real, and
  it would still only exercise the MAC.

**The ceiling, stated plainly.** Both of those produce `SIMULATED` evidence.
Neither answers range, throughput, power draw, thermal behaviour, antenna
performance, or HaLow and LoRa coexisting in one band centimetres apart. Those
are `TBR-RF-01`, `TBR-RF-02`, `TBR-RF-03`, `TBR-PWR-01` and `TBR-THERM-01`, and
they need radios. **Simulation extends what can be decided before the BOM. It
does not remove the BOM.**

## Bench, stage, evidence

Three related things, kept apart on purpose:

- **`test/bench/`**, here: *how* to take a measurement. A procedure, reusable
  across many runs.
- **`test/stages/`**: *what* must be demonstrated to qualify a build, with pass
  criteria.
- **`docs/evidence/<TRADE-ID>/`**: the results that close a trade.
  **`test/results/`**: the results of a stage run.

A bench procedure is written once and cited from wherever it is used. A
procedure copied into three trade documents will diverge in three directions.

## What a bench procedure must contain

- **What is measured**, in terms someone else could repeat.
- **Instrumentation**: instrument class, model, and where calibration matters,
  the calibration expectation. A measurement whose instrument is unrecorded
  cannot be compared with another.
- **Setup**, including a diagram where the physical arrangement matters. For RF
  it always matters: antenna type, orientation, separation, and what else is in
  the room.
- **Conditions to record**: ambient temperature, supply voltage, image build,
  region profile, what else was transmitting.
- **Procedure**, step by step.
- **What to record**, and in what form. Raw output is preferred over a summary.
- **Known sources of error**, and how to avoid them.

## Procedures this program will need

None is written. The trades that will demand them:

| Procedure | Trade |
| --- | --- |
| Throughput and latency between nodes at recorded separation | `TBR-RF-01`, `TBR-RF-03` |
| Receiver sensitivity with and without an in-band interferer | `TBR-RF-02` |
| Current draw at idle, at duty cycle, and at sustained maximum | `TBR-PWR-01` |
| Pack discharge to protection cutoff under representative load | `TBR-PWR-01` |
| Internal, component, cell and surface temperature under load | `TBR-THERM-01` |
| Real-time clock drift over a recorded interval and temperature range | `TBR-TIME-01` |
| Service and network plane resource use under load and at peak | `TBR-COMP-01` |

## The measurement rule

An unlabelled number in a text file is not evidence. Every measurement records
what was measured, the instrument, the date, the node, the image build, the
configuration, the ambient conditions, and who took it. See
`docs/evidence/README.md`.

Coexistence measurements in particular must be taken **in the assembled
enclosure**, at the antenna separations physically achievable there. A bench
measurement with the radios far apart does not answer `TBR-RF-02`.
