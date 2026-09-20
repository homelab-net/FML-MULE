# Development roadmap

## What this file is

The build sequence: what to work on next, in what order, and why. It exists
because targets were being picked conversationally, and twice the wrong one was
picked. It is hand-maintained and it will go stale; correct it in the same
change that invalidates it.

It is not the milestone. `ROADMAP.md` at the repository root holds the single
milestone, `v0.0.1`, and nothing here reorders that. It is not the qualification
plan; `docs/verification/` holds the thirteen stages and the ITEP. It is not the
generated view of decisions and trades; `STATUS.md` is, and it is regenerated
rather than edited.

| You want | Read |
| --- | --- |
| The one milestone the program is aiming at | `ROADMAP.md` |
| What is decided, what is open, what is on the critical path | `STATUS.md` |
| How a thing gets qualified, and on what rig | `docs/verification/` |
| What to build next and how to not get it wrong | this file |

## Phase intent: evidence over architecture

The program has enough architecture to build against. The dominant uncertainty
is now physical -- the Linux/radio boundary and RF coexistence -- and no design
reduces it. So the governing objective for this phase is to **reduce the number
of important assumptions not yet confronted with real hardware**, not to make the
architecture more complete. `AGENTS.md` ("The current objective") carries the
per-task rule; this section carries the demonstration ladder it serves.

Every phase ends with a **demonstration, not a document.** Each gate is a
physical result:

| Gate | Success |
| --- | --- |
| **M0** Reproducible platform | A clean supported machine produces the node image from pinned inputs. (The `GAP-09` register work, largely Codex's.) |
| **M1** Physical single node | One physical node cold-boots, creates its EUD AP, reports health, and serves one real local service to a phone. **This is `v0.0.1`.** |
| **M2** Two-node IP | Two physical nodes form the selected IP mesh and exchange traffic with no manual repair. |
| **M3** Fault and reconvergence | A bearer interruption, node restart, and topology change produce bounded failure and automatic recovery. |
| **M4** Useful mission function | Two EUDs on different nodes exchange mission data with WAN down. TAK belongs here. |
| **M5** Multi-bearer | HaLow, conventional Wi-Fi, and the degraded bearer run concurrently with characterized interference. |
| **M6** Power and thermal | The representative workload meets measured runtime and thermal limits on the candidate power architecture. |
| **M7** Integrated field article | The intended mechanical configuration repeats the earlier qualification without unacceptable regression. |

This ladder **refines, and does not reorder,** the phases under "Development
phases toward the prototype and v1.0" below and the `v0.0.1` milestone in
`ROADMAP.md`: M0-M1 are Phase P1 (`v0.0.1`), M2-M5 are the network and service
planes on real radios, M6-M7 are Phase P2's hardware article. RoIP and other
increments insert where operationally justified; they do not disrupt this
sequence. The pacing item ahead of M1 is **procurement** (the `HW-01` trades),
which is the Program Owner's decision -- so the near-term software contribution
is the tooling that makes the eventual demonstrations legible: instrumentation,
the deployment path, and automated evidence collection, not more architecture.

## Before you touch anything

Do these three things in order. They take about fifteen minutes and they are
the difference between contributing and creating work for somebody else.

1. **Read `AGENTS.md`.** It is the rules, not an overview. The table under
   "Before you write" is the one people skip and then violate.
2. **Read `STATUS.md`.** It tells you what is settled and what is open. Do not
   guess at either, and do not re-decide something that has an ADR.
3. **Run `tools/lint.sh` and read its exit code.** You need to know the tree was
   clean when you found it. The last line of output is not the result.

Then, for whatever you are about to touch:

| Area | Read first |
| --- | --- |
| Anything in `mule/` | `mule/README.md`, `FML-ADR-051`, `FML-ADR-052` |
| Anything in `os/` | `os/README.md`, `FML-ADR-040`, `os/kernel/PINS.md` |
| Anything in `test/` | `test/README.md`, `test/flatsat/README.md` |
| A hardware reading | `docs/readings.md` before writing the interface, not after |
| A new decision | `docs/adr/README.md`, then `tools/new-adr.sh` |
| A new open question | `docs/trades/README.md`, then `tools/new-trade.sh` |
| Anything touching radio | `REGULATORY.md`, and the region profile mechanism |
| Anything touching keys, identity or capture | `SECURITY.md`, `THREAT_MODEL.md` |
| Scope you think is missing | `docs/NON-GOALS.md` first; it may be refused on purpose |

## How this program actually gets things wrong

Every item below is real and from this repository. They are listed here rather
than only in `AGENTS.md` because they are the specific mistakes that cost this
program the most time, and a new contributor will make them again.

**A check that cannot fail.** Six have now been found. A convergence gate that
matched a column header and passed after one second. An `ip neigh flush` that
does not remove permanent entries, so the step it guarded printed success. A
regulatory comparison against the field it had just been copied from. A `bats`
test planting a status value that had since changed, so the `sed` matched
nothing. A single-hop step that exited zero on both paths. A fake that returned
the answer the code under test was supposed to decide.

So: **break it on purpose and watch it fire, when you write it, not later.** And
remove *every* instance of what it looks for, not one. The bridge check in
`tools/validate-docs.sh` was watched to fail on five spellings and the first two
versions each passed one of them silently. Reading them would not have caught
it.

**An instrument that cannot resolve what it is reporting.** A warm-up figure of
"22 seconds" was seven iterations of a loop costing three seconds each. Three
configuration verdicts were drawn from it and all three were inside its own
resolution. All three were retracted. Before quoting a number, state what the
measurement's resolution is; if you cannot, you do not have a number.

**Reporting a run's verdict as its inverse.** Two runs ended on a step that
passed, and the passing verdict was read as its opposite because the overall
run was red. Two further runs were built on the inversion. Read the signal that
means success, not the one that looks like it.

**A retraction appended below the claim it retracts.** The file then asserts
both, and a reader reaches the claim first. Replace the text; do not annotate
it.

**Testing the interesting case before the boring one.** Five runs went into
multi-hop mesh routing when no two nodes could exchange a packet at all. Test
the single-step case first; a failure in the interesting case is uninterpretable
until the boring one passes.

## The three tracks

| Track | What it is | CONOPS basis | Gated by | Who can do it |
| --- | --- | --- | --- | --- |
| 1 — Network plane | The multi-bearer mesh. The product. | 1, 39-45 | Mostly nothing | Anyone, no hardware |
| 2 — Hardware | Boards, radios, batteries, and the trades they close | 78, 82 | A purchase | Whoever has the hardware |
| 3 — Analysis | `TBR-TAK-01` and the decisions behind the blocked services | 26, 27, 30.2 | A named owner | Anyone, needs the Program Owner |
| 4 — Mission-service plane | TAK, voice, and the services on the node | 9, 26, 27, 45 | A selection, and `CCR-03` for voice | Anyone, some needs hardware |

**Every item cites its CONOPS basis.** A roadmap item exists to close a CONOPS
obligation or to build what one requires; an item that maps to no CONOPS section
is either mis-scoped or a gap in the CONOPS, and the coverage map at the end of
this file is where that is checked. The rule is the same one the traceability
matrix applies to requirements: a point with no allocation is a defect.

Track 1 is the default. If you are picking up this repository with no hardware
and no special context, work Track 1 from the top.

## Development phases toward the prototype and v1.0

The three tracks above say *what* to build and *who* can build it. This section
says how that work composes into the arc the program is actually on: from
software that runs on the bench, to a hardware architecture evidenced well
enough to order a BOM and build prototype units, to a `v1.0` a team can carry
into a field test.

**These are dependency phases, not a schedule, and not milestones.**
`ROADMAP.md` holds the one committed milestone (`v0.0.1`) and deliberately
schedules nothing after it; this section adds neither milestones nor dates, it
records the order the dependency structure forces. It **duplicates no `State:`
line** -- each phase is composed by reference to the tracks, banks and items
whose own `State:` lines remain the single source of their status. A phase
"exits" when the items it names have, by their own lines, reached the gate
described; nothing here is done until those are. Read the phases as gates and
work the tracks: the phases only tell you which gate the work in front of you is
aimed at.

### Phase P1 -- prototype-ready software

**The outcome.** Every plane that does not need a radio to exist is built and
exercised end to end on the bench -- against the flat-sat fakes and the one real
EUD -- so that when hardware arrives the first build is integration, not
discovery.

**What composes it, by reference.**

- `v0.0.1` (`ROADMAP.md`): one node, one service, reachable from a phone,
  cold-start-drill clean. The first real exercise of `os/image/` and the access
  point data path (`1.3`).
- Track 1, items `1.1`-`1.8`: the LoRa/Meshtastic waveform (`1.1`), bring-up
  sequencing (`1.2`), addressing (`1.4`, `1.5`, `1.5a`), `RadioState` (`1.6`),
  and the `batman-adv`/802.11s template (`1.7`, `1.8`) -- each worked to the
  software half its `State:` line allows without radios.
- Bank A, the software-only closures: the TAK service as three Quadlet units
  (`4.1`), on the `TBR-TAK-01` acceptance already recorded (`FML-ADR-071`).
- Bank B, the software halves that make a later trade a measurement rather than a
  design: `TBR-COMP-01` size (banked), `TBR-MAP-01` (`4.4`), bring-up and
  `RadioState`, and the mesh template.
- The former coverage-map gaps that are pure software: time (now item `4.5`) and
  identity and admission (now item `4.6`) have dedicated items; the storage-at-rest
  and recovery readers (`TBR-SEC-01`, `TBR-REC-01`) still await theirs. Phase P1
  is where these get their own Track 4 and Track 1 items.

**Exit gate.** The flat-sat exercises every non-physical plane end to end against
fakes plus the real EUD; `v0.0.1`'s drill passes; and every remaining open trade
on the path is, by its own `State:` line, waiting only on a hardware measurement
or an owner's act -- not on more software design.

**CONOPS basis.** 1, 4, 5 (local-first); 6 (`1.3`, `1.4`); 9, 9.2 (Track 4,
`4.4`); 26, 27 (Track 3, `4.1`); 39-44 (Track 1); 50, 51 (`1.6`).

### Phase P2 -- a hardware architecture evidenced enough to build

**The outcome.** The decisions that *choose* the BOM are made on bench evidence,
the BOM is committed, prototype units are built, and the physical trades become
measurements with a known method rather than open designs. This is the "before
any prototype material is ordered" goal in "Before the BOM" below, and then the
build itself.

**What composes it, by reference.**

- Bank C, the BOM-choosing decisions, made before the purchase: `TBR-RF-03` (AP
  and mesh consolidation -- the hinge the others turn on), `TBR-CARRIER-01` (the
  M.2 slot, radio or storage), and `TBR-COMP-01`'s hardware axes (memory class,
  storage), each informed by the Bank B software measurements.
- `hardware/prototype/`: the open BOM cells (a committed SSD, the Wi-Fi board
  count) resolve once Bank C is set, and the purchase is made against a de-risked
  design.
- Track 2, day one: the moment hardware arrives, run the existing flat-sat
  scenarios against real interfaces to find which fakes were lying
  (`test/flatsat/README.md` is the day-one test plan), after which bring-up
  follows the `1.2` sequence instead of being an experiment.
- The physical trades, now measurements on the ITEP rigs: `TBR-RF-01`,
  `TBR-RF-02`, `TBR-RF-03`, `TBR-PWR-01`, `TBR-THERM-01`, `TBR-LINUX-01`,
  `TBR-HW-01`, `TBR-CARRIER-01`, and `TBR-COMP-01`'s hardware half. Power and
  thermal get the Track 2 roadmap items the coverage map notes they lack.

**Exit gate.** The BOM is committed on evidence; at least one prototype unit is
built and boots the image; bring-up runs the known sequence on real radios; and
the physical trades have first measurements under `docs/evidence/` accepted by
their owners. This is the smallest, cheapest first build the evidence allows.

**CONOPS basis.** 78, 79, 82, 85 (qualification stages and verification -- Track
2 and the ITEP).

### Phase P3 -- `v1.0`, the multi-bearer product, into a field test

**The outcome.** The features `v0.0.1` deliberately excluded come back in on real
hardware -- the IP mesh, the sub-GHz and LoRa planes, the TAK-compatible service
plane, identity and mission trust, and A/B update and rollback -- integrated on
prototype units and taken into a field test against the CONOPS operational
scenarios.

**What composes it, by reference.**

- The network plane on radios: the mesh (`1.7`, `1.8`), the LoRa/Meshtastic plane
  (`1.1`), and multi-node routing, now measured rather than simulated.
- The mission-service plane, Track 4: the TAK service (`4.1`) and the map service
  (`4.4`) deployed from the catalog once the catalog gate opens (`TBR-HA-01` and
  the catalog decision, both the owner's), and the placeholder services
  (`status-aggregator`, `mission-trust`, `service-controller`, `gateways`) built
  behind the interfaces their blocking trades then permit.
- Identity and mission trust (`TBR-ID-01`, `FML-ADR-036`/`037`/`038`) as a
  first-class Track 4 item, and the diagnostic tier (`FML-ADR-046`, CONOPS 52).
- The recovery and update path (A/B, rollback), excluded from `v0.0.1` by design.

**Not in `v1.0`.** The RF voice gateway / RoIP (`4.2`, `4.3`) is a CONOPS v1.1
change gated on `CCR-03`, not a `v1.0` feature; it stays off `v1.0` scope for the
same reason `docs/NON-GOALS.md` carried it. Naming it here keeps it from drifting
back in. EUD-native voice and video (`4.8`) -- softphone and in-app video for a
user carrying no radio -- is a *later* increment still: `FML-ADR-067` places
direct-to-headset and non-radio audio outside the v1 baseline, so it sits beyond
even the v1.1 RoIP work and must not be conflated with it.

**Exit gate.** A `v1.0` build runs the CONOPS operational scenarios across more
than one node in a field test, with evidence under `docs/evidence/` and
`test/results/`. `v1.0` is the first version that promises anything about the
interfaces it exercises; `v0.0.1` promised nothing, by design (`ROADMAP.md`,
versioning).

**CONOPS basis.** 1, 39-44 (the mesh product); 9, 9.2, 26, 27, 45 (services and
external RF); 46 (`CCR-03` governance); 52 (diagnostics); 86 (change control).

### What this phasing does and does not change

It **reorders nothing**: the tracks and their `State:` lines are unchanged, and
the sequencing rules under "Sequencing" below still say what to work next. It
adds a *reading* of the same items -- which gate each is aimed at -- so an owner
can see the arc from bench software to a fielded `v1.0` without it becoming a
schedule. If a phase here ever contradicts a track item's `State:` line, the
`State:` line is right and this section is stale.

## Track 1 — the network plane

### Where it stands

Real, and `SIMULATED`. `.github/workflows/mesh-probe.yml` builds a three-node
batman-adv mesh in network namespaces over `veth` and routes traffic two hops
across it, on every push that touches it. It asserts single hop, two hops, ARP
resolving unaided after the caches are deleted, that node1's originator entry
for node3 names node2 as next hop, and that a cold mesh carries traffic within
ten seconds of attach.

Five values in `os/config/batman-adv.conf.template` are no longer `TBD`, and
each carries how it was obtained:

| Value | Basis |
| --- | --- |
| `routing_algo=BATMAN_IV` | `FML-ADR-053`. BATMAN_V is absent from the stock module. |
| `hard_interface_mtu=1560` | The kernel names the figure on every interface add. |
| `bridge_loop_avoidance=0` | `FML-ADR-056`. Measured: 31.5s against 2.150s. |
| `multicast_mode=0` | Reasoned, not measured. Says so. |
| `distributed_arp_table=0` | Reasoned, not measured. Says so. |

**What that does not mean.** The link layer is a `veth` pair: a perfect wire,
with no propagation, loss, contention, rate adaptation, desense or range. Every
quantity `TBR-RF-01`, `TBR-RF-02` and `TBR-RF-03` exist to measure is absent. A
mesh forming here says nothing about a mesh forming in a car park.

802.11s cannot be exercised on a GitHub hosted runner. The Azure kernel flavour
carries no wireless stack at all, and `linux-modules-extra` supplies
`batman-adv` but no wireless driver, `mac80211_hwsim` included. The probe checks
for a wireless stack on every run and reports what it finds, so the day that
changes the file discovers it rather than someone assuming it.

### 1.1 LoRa and Meshtastic — the largest hole

**State:** all four steps done. What remains on this plane is not this item:
the member tag is specified and measured but unimplemented, and the gateway
that would carry it is blocked on `TBR-TAK-01`.
`.github/workflows/lora-probe.yml`
stands two meshtasticd nodes up in simulation on one segment and asserts a text
message crosses between them. Three runs: the first died on a line of mine that
printed a version and tested nothing, the second found that a configuration
change reboots the daemon, the third passed. `SIMULATED`, and the transport is
UDP on a Docker bridge, which is a perfect wire.

Beyond that probe the plane had been one `Literal` in `mule/bearers.py` and two
references to it. It now has an interface and a fake; it still has no
configuration.

**Why it is first:** `FML-ADR-026` makes LoRa the degraded-mode lifeline. It is
what users fall back to when everything else has failed, which makes it the
bearer whose failure is least tolerable and the one with the least behind it.
It is also testable in software, the same way batman-adv turned out to be:
Meshtastic runs over a TCP or serial simulation with no radio present.

**Blocked by:** nothing any more, in substance. The question step 2 waited on —
whether a node is one Meshtastic identity or a gateway fronting four to eight
EUDs — is answered by
`docs/evidence/TBR-NET-02/2026-08-29-addressing-specification.md`. A MULE is one
Meshtastic node, several users behind it collapse to one address, and the
recipient rides in upstream's own fields -- `Contact.callsign` and `GeoChat.to`
-- per `FML-ADR-070`, rather than a custom tag.

The trade is now `CLOSED` (`FML-ADR-070`, 2026-09-04): the specification was
enough to shape an interface against, and the owner's acceptance of the
upstream-field encoding made it final rather than replacing the interface built
to it.

**The gap is now only the signature.** Checked item by item, the specification
satisfies all five closure-evidence items and the closure gate's additional
condition, that it state what changes when `TBR-ID-01` closes and what does
not. Nothing in the gate is outstanding except a named owner accepting it.

The specification withheld closure on a second ground as well, that nothing
exercised an EUD behind one MULE reaching an EUD behind another. That ground
was always stronger than the gate requires -- items 1 to 4 may be produced by
analysis on rig R0 or R1, and item 5 needs no rig -- and it has since been met
in simulation by the EUD leg in `.github/workflows/mesh-probe.yml`. It should
not be read as a technical blocker any more.

**Read first:** `TBR-NET-02` and `FML-ADR-057` before anything else, because
they decide what the interface addresses. Then `FML-ADR-026` for why it is a
separate non-IP plane and what
that forbids. `docs/interfaces/` for what crosses between planes.
`mule/bearers.py` for the vocabulary that already exists. CONOPS section 5.5
for where LoRa sits on the degradation ladder, and section 9 for service
criticality, because what may cross this bearer is a criticality question.

**Build, in this order:**

1. ~~A probe in CI that runs two Meshtastic instances against each other in
   simulation and passes a message.~~ Done. `.github/workflows/lora-probe.yml`.
2. ~~**`TBR-NET-02` first.** Not code.~~ Done. The specification is under
   `docs/evidence/TBR-NET-02/`, and it decides that the interface addresses a
   node, with the user carried as a tag inside the payload.
3. ~~Whatever narrow interface that justifies, with a fake, named in
   `test/flatsat/README.md`.~~ Done. `LoRaPlane` and `FakeLoRaPlane` in
   `test/flatsat/`, not `mule/`, because `FML-ADR-052` condition 4 keeps an
   interface whose shape an open trade governs out of the production package.

   Building it found a defect rather than only adding surface. `mule/status.py`
   answered CONOPS section 67 question 10 with `"lora" in associated`, and
   association means "mesh peer, or AP serving": an 802.11 question asked of a
   plane `FML-ADR-026` makes non-IP, which this file's own traps section warns
   about. Combined with the probe's finding that the daemon exits on a
   configuration change, a node could report the lifeline available while
   nothing could carry. The interface reads whether the stack answers instead,
   and `None` -- the platform cannot tell -- reads as unavailable.
4. ~~Only then, configuration templates under `os/config/`.~~ Done.
   `os/config/meshtasticd.conf.template`. It has no `networkd` in it, because
   `FML-ADR-026` makes the plane non-IP: no address, no bridge, no place in IP
   routing.

   The supervisor is the part the file exists to state, and it is a `shall`
   rather than a preference because the probe demonstrated the failure twice:
   a configuration change reboots the daemon and the re-exec fails, so a push
   can leave the lifeline dead, silently. The supervisor restarts on exit and
   does not call a push complete until the API answers.

   **How the daemon is deployed is left open, deliberately.** `FML-ADR-029`
   makes rootless quadlets the default for workloads that "do not require
   privileged hardware", and `meshtasticd` needs a serial device, so it is
   outside that default by the ADR's own terms. Nothing has decided what
   replaces it and the template does not: that is an ADR, and it interacts with
   an image build that does not exist.

**Done when:** the interface exists, the flat-sat exercises it, and
`test/flatsat/README.md` names any fake added. All three are met. Step 1's own
gate — a message asserted across in CI rather than printed — is met.

**What step 3 did not do.** It encodes no member tag, no node number and no
recipient. Those are `TBR-NET-02`, and the position on that trade has changed;
see below.

**Traps:** it is a *non-IP* plane by decision. Do not give it an address, do not
bridge it to `bat0`, do not let it inherit the IP plane's vocabulary. If you
find yourself wanting to, that is a change request against `FML-ADR-026`, not an
implementation detail.

Two things the probe established that cost a run each to find. **Changing a
node's configuration reboots it**, and in the container image the re-exec fails,
so the process exits; that is why the probe supervises its nodes and waits for
the API to return. It belongs to item 1.2 as much as here. And **`Data.dest` is
a node number**, not a user, which is the whole of `TBR-NET-02` in one field.

### 1.2 Interface bring-up sequencing

**State:** done as far as this repository can take it without hardware. The
ordering is machine-checked, the configuration is templated, and the units are
described in `os/config/systemd-units.template`. `mule/bringup.py` holds the order as constraint
pairs, `violations` catches a sequence that broke one, and `state_violations`
checks the invariants a wrong order leaves detectable on a finished node while
saying which two leave no trace. `FML-ADR-059` is `SELECTED` and
`os/config/networkd.conf.template` describes the file set against it, every
value `TBD`. What is missing is the systemd units that order
`wpa_supplicant` against `networkd`, which is the seam the template says it
cannot express.

**Blocked by:** nothing. This is sequencing, and it is what makes a node a node.

**Read first:** `os/README.md` for the two-layer split, `FML-ADR-040` for the
compatibility set, `os/config/*.template` for what has to be applied, and
`os/ansible/` for the shape the configuration pipeline already has.

**Build:** the ordering, as systemd units. Radio up, mesh join, `batctl
interface add`, `bat0` up, address, announce, access point up. `batman-adv`
attached to an interface that is not yet up fails in a way that looks like a
radio fault, which is why the order is the deliverable.

Note two things the probe established that the units must carry:
`routing_algo` is set **before** any interface is added to the mesh, and the
hard interface MTU is 1560 **before** the add, not after.

**Done when:** the units exist, the flat-sat exercises the sequence end to end,
and a wrong order fails a test rather than producing a mesh that looks up.

Two things belong here that were found elsewhere. `FML-ADR-056` gives up
automatic loop protection and asks for a **loop detector** in exchange: a
client address under more than one originator, or the node's own bridge address
arriving from the mesh, are both readable with `batctl`. And the LoRa probe
established that **changing a node's configuration reboots the daemon**, so
whatever supervises `meshtasticd` needs a restart policy; a config push that
leaves the lifeline bearer dead is the worst failure this system has.

**Traps:** the network management stack is undecided, and
`os/config/interfaces.conf.template` says so. Do not decide it silently by
writing units for one. If the sequencing work forces that choice, it needs an
ADR.

**It forced that choice, and the item split because of it.** The ordering half
is done: `mule/bringup.py` holds it and a wrong sequence fails a test.

The units were the other half and could not be written without saying who owns
link configuration. **`FML-ADR-059` is now `SELECTED` and says
`systemd-networkd` does**, with `wpa_supplicant` and `hostapd` keeping
association, and mesh attachment expressed in `networkd` configuration:
`Kind=batadv` with `RoutingAlgorithm=` and `BridgeLoopAvoidance=`, and
`BatmanAdvanced=` on the member link.

Read that ADR's consequences before writing them, because it names the cost it
took on. Ordering stops being something the node performs and becomes something
a component resolves, and `networkd` does not report the order it used. The
wireless half is still outside it: `networkd` does not create an 802.11s mesh
point interface, so the dependency between `wpa_supplicant` having associated
and `networkd` attaching that link is a unit ordering that can be got wrong
silently. That seam is where this work is most likely to go wrong.

### 1.3 The access point data path

**State:** mostly decided, and the decisions were got wrong once. `FML-ADR-054`
and `FML-ADR-055` were both written on the premise that the mesh interface is
bridged to nothing. SAD section 4.3 bridges local EUD access into the BATMAN
domain, so the premise was false and both are superseded, by `FML-ADR-056` and
`FML-ADR-057`.

What is settled now: bridging the access point to the mesh interface **is** the
design; the bridge carrying it holds only access point interfaces; a wired link
carrying field traffic joins the mesh with `batctl` rather than the bridge; a
management link is routed. Loop avoidance stays off, by Program Owner
direction, and the shared-LAN case is handled by that structure rather than by
paying the warm-up.

What is left in the file: the bridge **name** and the interface naming around
it, which wait on `TBR-RF-03` and `TBR-LINUX-01`. `ap_isolate` follows
`FML-ADR-057`: stations are not isolated, because that is what peer ATAK
between two people at one MULE runs over.

**Blocked by:** naming only, and the loop detector is no longer part of it.
`mule/loops.py` implements the two signatures `FML-ADR-056` names, with a fake
and a test per signature. `ap_isolate` is decided rather than `TBD`:
`FML-ADR-057` settles it and the template now says so. What is left is
`bridge=`, which is `TBR-LINUX-01`.

**Read first:** SAD section 4.3, which is short and settles more than any of
the ADRs around it. Then `FML-ADR-056` and its accepted cost, which is the one
that creates work: loop protection is now structural rather than automatic, and
the ADR calls for a loop detector that does not exist. Then `FML-ADR-057` for
what the node can and cannot see, `FML-ADR-045` for why the access point and
the mesh are separate radio functions but not separate layer 2 domains, and
`TBR-NET-01` and `TBR-NET-02`.

**Why it matters now:** `FML-ADR-056` keeps bridge loop avoidance disabled, and
what makes that safe is a rule rather than a measurement: the bridge carrying
the mesh interface holds only access point interfaces, and anything reaching a
segment another node reaches stays out of it. The Program Owner records that
several nodes are likely to share one LAN during configuration, during
over-the-air update, and in a tactical operations centre. Sharing a LAN is
safe; bridging it into the mesh is not.
`tools/validate-docs.sh` check 19 enforces the pairing and will fail the build
if this is answered carelessly.

**Done when:** `bridge=` and `ap_isolate` carry values consistent with
`FML-ADR-056` and `FML-ADR-057`, check 19 still passes, and the loop detector
`FML-ADR-056` calls for either exists or is recorded as work with a home.

### 1.4 `TBR-NET-02`, how a node addresses the EUDs behind it

**State:** the analysis half is produced and one of its findings is
demonstrated. `docs/evidence/TBR-NET-02/2026-08-29-addressing-specification.md`
carries all five artifacts the closure gate lists. The mesh probe now proves the
finding that artifact itself flagged as untested: an EUD behind one MULE reaches
an EUD behind another, two hops away, and the far node holds it as a global
translation-table entry rather than a local one.

**The decision is made and the trade is `CLOSED` (2026-09-04).**
`2026-08-30-opentakserver-meshtastic-path.md` read the first of `FML-ADR-048`'s
three gateways and found two things. A payload on a private port is discarded by
it, which is where a custom one-byte member tag would sit. And the ATAK plugin
protobuf it does handle already carries `Contact.callsign` and `GeoChat.to`, so
identity and recipient are on the wire already, as upstream's strings rather than
this program's index.

So the specification's chosen encoding was not available in combination with
`FML-ADR-048`: adding the index means replacing upstream's format, which that ADR
orders the program not to do first. The Program Owner chose **using what upstream
carries** -- `Contact.callsign` and `GeoChat.to` -- accepting the higher airtime,
recorded as **`FML-ADR-070`**. Two follow-ups fall out of it, tracked as
consequences rather than open trade parts: an artificial composition character
limit sized to the 231-byte usable payload (step 2 below), and confirming what
`GeoChat.to` contains before recipient resolution is built.

**Blocked by:** nothing. `TBR-ID-01` is deliberately not a prerequisite: this
trade exists to structure addressing so authentication can be added to it later
rather than redesign it.

**Read first:** the trade, then `FML-ADR-057`, which states which traffic the
node may act on and which it may not, and therefore bounds every option in the
trade. Then
CONOPS section 6 for why the shared case is the normal one, section 23 for why
a recipient tag is addressing rather than confidentiality, and section 9 for
which services are even present when LoRa is carrying the traffic.

**The shape of it:** three identity namespaces exist and nothing maps between
them. ATAK has a CoT UID and callsign, browser services will have whatever
`TBR-ID-01` decides, and Meshtastic has a node number. `Data.dest` addresses a
node, so several users behind one MULE collapse to one address on the bearer
CONOPS section 50.8 makes the lifeline.

**Done when:** the four artifacts in the trade's closure evidence exist under
`docs/evidence/TBR-NET-02/` and a named owner accepts them. **Done 2026-09-04:**
`TBR-NET-02` is `CLOSED`, the owner accepted the specification, and the encoding
is `FML-ADR-070`.

**Implemented so far:** the two rules that need no roster are built in
`mule/recipients.py` (pure functions under `FML-ADR-052`): the 231-byte payload
budget a message plus its identity fields must fit (`FML-ADR-070`), and the
fail-closed delivery decision -- deliver, redirect to a configured default, or
refuse, and **never** broadcast. Still deferred and passed in rather than derived:
the participant **roster** (a mission-schema change this trade declined, later
`TBR-ID-01`'s) and the `GeoChat.to` parser that yields a recipient key.

**Traps:** the natural implementation of "cannot resolve the recipient" is to
deliver to everyone. It looks like helpfulness and CONOPS section 23 makes it
wrong, which is why the trade states the fail-closed rule as a gate rather than
leaving it to the analysis.

### 1.5 `TBR-NET-01`, the addressing plan

**State:** **`CLOSED` 2026-09-04.** The decision is **`FML-ADR-063`,
`SELECTED`**, and the named owner accepted the evidence. All three
closure-evidence items exist under `docs/evidence/TBR-NET-01/`: the third,
that the mission schema validates a deployment's addressing configuration, was
the change `FML-ADR-063` required but did not make, and was supplied 2026-09-04
by constraining `network.address_prefix` to a per-deployment IPv4 CIDR with a
machine-checked counter-example (`2026-09-04-schema-validates-addressing.md`).

The decision: the field prefix is **per-deployment**, generated not derived from
identity, and a node **never carries an overlapping uplink silently** --
detection is required, silence is prohibited. IPv6 was excluded 2026-08-31 for
broader hardware support and older EUDs, which closed the option space to IPv4;
RFC 4193 ULAs would have answered the question but were ruled out on that ground,
recorded with a disposition. What a node *does* about an overlap beyond reporting
it is left to service-plane policy (`TBR-TAK-01`, `services/`).

`FML-ADR-063` being `SELECTED` also **met the condition on `FML-ADR-061`'s
liaison half** (1.5a): per-deployment prefixes are what a routed liaison needs.

The interoperability exercise is done. Two independently configured deployments
sharing
the prefix conflict **silently** -- one node wins ARP consistently, the loser
resolves its peers, marks them `REACHABLE`, and cannot talk to them, with no
kernel message and nothing in `batctl` to explain it.

The other half of that exercise is done too. Deployments with **different**
prefixes coexist completely -- one mesh, every originator known, neither
degrading the other -- and do not interoperate at all, failing at the sender
with `Network is unreachable` before a packet leaves. ATAK-style multicast does
not cross either, and `batman-adv` is not what stops it: Debian ships
`rp_filter = 2`, so a datagram whose source has no route is dropped by the
receiving kernel. One on-link route per side restores both, with `rp_filter`
untouched.

So the choice is between a silent failure and a loud one, which is an argument
and not a decision.

**Both of those assumed a premise the schema contradicts, and a third exercise
now tests the default case.** `mission/schema/mission-package.schema.json` says
network identity values differ between deployments, and `mesh_id` is required.
With different `mesh_id`, two deployments never share a layer 2 domain: even
identical prefixes and identical host addresses are harmless, measured. So the
collision is not what happens when deployments meet, it is what happens once
they **deliberately converge** on one mesh identifier.

**That makes `mesh_id` upstream of this item, and nothing owns it.** No trade
and no ADR decides whether it is per-deployment, program-wide or negotiated at
an incident. Deciding the prefix without it settles a consequence before its
cause: if `mesh_id` always differs, deployments can never interoperate and the
prefix hardly matters; if they can agree one, the prefix matters entirely.

**That gap is now `TBR-NET-03`, item 1.5a, and this item depends on it.**

**The collision analysis is now done too, and it reframes this item.** Any
external route more specific than the mesh `/16` silently takes that slice of
the mesh away while the rest keeps working -- a venue LAN on `10.41.5.0/24`
removes exactly the mesh nodes in that range, and a `/17` from a Tailscale
subnet router removes half the field prefix. Nothing warns, because
longest-prefix match is behaving correctly. **The failure is not a property of
`10.41.0.0/16`**: any fixed prefix behaves identically, so selecting a different
one cannot remove the risk. What is needed is a rule about how the node routes,
not what it is numbered.

All three closure-evidence items now exist. Still missing: the decision itself,
which needs 1.5a first, and which the third artifact argues cannot be a pure
prefix choice.

**Read first:** the trade itself, `os/config/interfaces.conf.template` for the
consequences already written down, and `THREAT_MODEL.md` — an address derived
from a durable node identifier is a durable identifier visible to anyone
observing traffic.

**The constraint people miss:** the scheme must not collide when two
independently built deployments meet at an incident. That rules out a fixed
prefix chosen once.

**Done 2026-09-04:** the evidence under `docs/evidence/TBR-NET-01/` was accepted
by the named owner and `TBR-NET-01` is `CLOSED` on `FML-ADR-063`.

### 1.5a `TBR-NET-03`, how two deployments converge

**State:** **`CLOSED` 2026-09-04**, on the named owner's acceptance, once
`TBR-NET-01` closed and lifted the sequencing gate. **The decision is
`FML-ADR-061`, `SELECTED`**, with five artifacts supporting it. `FML-ADR-060`
was superseded the day after it was written and must not be read as current.

The mesh is keyed with `key_mgmt=SAE`, MULEs of one deployment merge
automatically on a shared credential, and a partner gets a **separate keyed
mesh** on a liaison node so the boundary is revocable without rekeying the
fleet. Measured: a node without the credential never reaches `ESTAB`;
`test/bench/keyed-mesh.sh` reproduces it.

**Closed the same day as 1.5, in that order.** The last unsupplied item -- what
a liaison may forward and who authorises one -- was supplied 2026-09-04
(`docs/evidence/TBR-NET-03/2026-09-04-what-a-liaison-forwards-and-who-authorises.md`:
default-deny, enumerated flows only, a liaison a declared authorised role rather
than a radio act). The trade's own gate held that a liaison mechanism is not
accepted while 1.5 was open; 1.5's per-deployment-prefix selection met
`FML-ADR-061`'s condition and 1.5 then closed, lifting the gate, so `TBR-NET-03`
closed on the owner's acceptance immediately after.

The routed-liaison option works end to end for one route per liaison, layer 2
never merges, and the collision is structurally unreachable. Two operational findings came with
it. **The mesh heals and a hand-typed route does not** -- after the bearer
bounces, 802.11s re-peers and `batman-adv` reconverges, while the kernel has
deleted the static route with its interface and does not restore it, so the
mechanism fails silently with a healed mesh and a reachable next hop. That is
a configuration management problem, and a second reason for `FML-ADR-059`. And
identical prefixes defeat the option
twice: the route cannot be installed, and no address exists that names the
other deployment's node. It exists because item 1.5
turned out to be answering a consequence: `mesh_id` is a required
mission-package field and separates deployments by construction, so the address
collision is reachable only once two deployments deliberately share a mesh
identifier, and nothing says how they would.

**Read first:** the trade, and the three artifacts under
`docs/evidence/TBR-NET-01/` in the order its README gives. The third one is the
reason this item exists.

**The constraint people miss:** a mesh identifier is transmitted in the clear in
802.11s beacons. A fixed program-wide value is a published constant identifying
a MULE deployment; a per-incident value agreed over voice is something an
adversary can hear. `THREAT_MODEL.md` has to be asked about whichever is
chosen, and the options differ in what they disclose rather than in whether
they disclose.

**It constrains 1.5's answer, not just its order.** Every mechanism 1.5a
considers fails while two deployments can hold the same prefix -- merging them
reproduces the collision, and a routing liaison cannot route between two
interfaces in the same subnet. So selecting any mechanism removes the
fixed-prefix option from 1.5. Deferral is the only branch that leaves it free,
and deferral still does not close 1.5, whose remaining item is a collision
analysis against external networks that no `mesh_id` answer touches.

**Work it before 1.5.** No hardware; the separation result came from
`mac80211_hwsim` and the convergence exercise can too.

**Done when:** a written decision naming one mechanism, or deliberately naming
none, accepted by a named owner. See the blocker in Track 3.

### 1.6 Turn `RadioState` into an implementation

**State:** built. `test/flatsat/interfaces.py` holds the Protocol,
`test/flatsat/radio_parse.py` the parse core, and `test/flatsat/radio.py` the
real reader `CommandRadio`: it reads `iw dev` and `iw station dump` through an
injected runner and returns `enumerated()`/`associated()`, with `None` wherever
it cannot tell. It is built exactly as `mule.sysfs.SysfsThermalReadings` is --
an injected per-board interface-to-`Bearer` map, empty until `TBR-HW-01`, and an
injected command runner so tests feed fixtures and a node runs the binaries.
Tested against `mac80211_hwsim` fixtures; mutations `M67`-`M70` hold the
`None`-versus-real-reading line.

**An earlier note here called this "blocked" on two counts and it was wrong.**
The `T | None` fix to the Protocol is applied inside the flat-sat, which is not
the promotion the interface note prohibits, and `modes.py` consumes tuples, not
the Protocol methods, so it was untouched. The per-board map is the same
injected-empty pattern `SysfsThermalReadings` already ships. Both were doable and
are done.

**What actually remains, and is smaller than it looked:** the reader lives in the
flat-sat, not `mule/`, because the interface is still held there pending
`TBR-LINUX-01`/`TBR-RF-01`/`TBR-RF-03`; it moves to `mule/` with the Protocol
when a production consumer wires it to `mule/modes.py`. And the per-board map is
empty until `TBR-HW-01` names a board, so on real hardware the reader returns
`[]`/`None` until that map is supplied -- which is the honest state, the same one
the thermal reader is in.

**Read first:** `test/flatsat/interfaces.py`, `test/flatsat/fakes.py`, and
`docs/readings.md` — **before** writing the interface, not after. Every reading
needs a row there and CI enforces it.

**Build:** actual code reading `iw dev`, `iw station dump`, `batctl
originators`. This is when `mule/modes.py` starts consuming something real
instead of a fixture.

**Traps, all three of which this repository has already made:**

- Prefer a kernel interface to a command. A command is a package in the image,
  a fork per reading, and output that is not ABI-stable. Where only a command
  exists, name the package that provides it.
- Put the unit in the method name. Linux reports the same quantity in
  millidegrees, tenths and percents depending on subsystem.
- Every reading a platform might be unable to provide is `T | None`. A type
  that cannot say "I cannot tell" has been the same defect four times.

### 1.7 802.11s, and the rest of the batman-adv template

**State:** unreachable in hosted CI. `orig_interval`, `hop_penalty`, `gw_mode`
and `fragmentation` remain `TBD`, and the figures previously recorded against
`orig_interval` measured nothing and say so.

**Blocked by:** a machine with a wireless stack. A local VM with
`mac80211_hwsim` is enough for 802.11s association; the RF quantities need
`TBR-RF-01` and real radios.

**Do not** re-derive the `orig_interval` figures on `veth`. The question that
parameter decides is convergence after a topology change on a lossy link, which
a perfect wire cannot pose.

### 1.8 Mesh WAN gateway sharing

**State:** target set, mechanism open, routing logic now demonstrated
`SIMULATED`. `FML-ADR-069` decides that WAN is a mesh-wide capability -- a MULE
with an uplink fans it out to WAN-less nodes, and several nodes' uplinks are
pooled -- as the CONOPS section 42 end state beyond the v1 single-gateway
baseline. `FML-ADR-068` is the node-local first step, an EUD reaching its own
node's uplink, demonstrated `SIMULATED` on the prototype access point. As of
2026-09-04 the mesh half is exercised too: `test/bench/wan-gateway-sharing.sh`
runs `batman-adv` gateway mode on `mac80211_hwsim` and a WAN-less node selects a
peer's gateway, reaches its uplink, fails over to the surviving uplink, and loses
only WAN on partition (`docs/evidence/TBR-NET-04/`, `SIMULATED`). The decision
that stays open -- single-active versus pooled multi-active, load-share versus
failover -- is `TBR-NET-04`. Its no-hardware half is now analysed
(`docs/evidence/TBR-NET-04/2026-09-15-single-active-versus-pooled-analysis.md`):
the bench, re-run with an added assertion, confirms `batman-adv` `gw_mode` is
single-active with failover, and records that multi-active pooling is not a
`gw_mode` feature and needs a mechanism above `batman-adv`. The throughput and
real-radio selection it also needs are hardware.

**CONOPS basis:** section 42 (any MULE may hold the local WAN-gateway role),
section 43 and section 744 (the MULE is the overlay boundary and EUD traffic must
not cross it), section 410 (the gateway is a property of the mesh, not of the
node an EUD sits on).

**Blocked by:** `TBR-NET-04`, and the `gw_mode` half of item 1.7. A local
`mac80211_hwsim` mesh can exercise gateway election and a WAN-less node reaching a
peer's uplink; the RF and real-uplink behaviour need hardware and `TBR-RF-01`.

**Do not** route EUD traffic onto the secure overlay while building this. CONOPS
section 43 and section 744 keep the MULE the routing and security boundary; the
firewall rules match the EUD prefix to the general uplink, never the overlay.

### 1.9 Mesh capability probing

**CONOPS basis:** section 67 (the operator view answering what a link can carry,
not raw routing tables) and section 40 (traffic preference). The probe is a
network-plane function under `FML-ADR-028`; the mission-service plane, including
the operator view (`4.7`), displays its result but does not run it.

**State:** forward policy, recorded so it is designed once rather than improvised.
The operator view wants a per-peer capability -- can this link carry video, voice,
or only text -- but `FML-ADR-053`'s BATMAN-IV metric is transmit-quality
(loss-derived), not throughput, so capability cannot be read from the routing
metric alone. The tiers those signals map to are named by `FML-ADR-080`, the
per-link view of the CONOPS section 50 ladder. Passive signals are the always-on
floor: TQ, the `iw` station PHY-rate ceiling, the bearer and the hop count
reliably rule a tier *out* and emit nothing; a light, paced, tier-sized active
probe is what confirms a tier *in*.

**One floor signal is not yet readable.** `test/flatsat/radio_parse.py` extracts
TQ and the PHY-rate ceiling, but there is no per-peer **hop-count** reading:
`batctl originators` gives a next hop, not a path depth, so `mule/capability.py`
receives `None` for hops today and skips that ceiling. A hop source -- batman-adv
translation-table depth, for one -- is an open sub-item before the hop dimension
of `FML-ADR-080` can contribute.

**The policy to hold:** the active probe **shall** send briefly at the target tier
rate rather than saturate the link (a `batctl tp` throughput test strains the
shared channel and flaps routes), **shall** be paced with jitter, a per-node phase
offset and a round-robin stagger, and **shall** skip or yield when the channel is
busy, so a fleet does not all probe on the minute. It **should** size to the tier
and step up, never video-probing a link that failed voice, and **shall** be
suppressed under EMCON.

**Read first:** `test/bench/mesh-traffic.sh`, which already measures the transport
half -- multi-hop latency and a voice-profile flow's jitter and loss under a bulk
flow -- `SIMULATED` on `mac80211_hwsim`, with its QoS qdisc illustrative and not a
decision (`TBR-RF-01` owns the mechanism).

**Done when:** `TBR-RF-01` sets the QoS and rate mechanism and the probe's real
airtime cost is measured on hardware -- whether a roughly one-minute cadence is
affordable is a measurement, not a paper call -- and the probe runs as a
network-plane function feeding the operator view's capability field, with the
decision entered in the register. Out of `v1.0` scope until that evidence exists.

## Track 2 — hardware

**State:** an Intel N150 system is selected as a development-only article under
GAP-09A, GAP-09B defines the Debian mkosi image mechanism, and GAP-09C now
defines the exact package closure, retained cache, CycloneDX provenance, and
repeatability/VM-boot gate under `FML-ADR-081`. No production hardware is
selected, no image is built, and nothing in this repository has met a radio.

**What the purchase should be made against.** `docs/readings.md` carries the
selection criteria that come from software rather than from the SAD, and they
are easy to discover too late:

- whether the RTC exposes a battery-low flag (`TBR-TIME-01`, `TBR-HW-01`);
- whether the battery management has a `power_supply` kernel driver;
- how the board reports thermal throttling, if it reports it at all;
- whether thermal zone `type` strings identify zones meaningfully.

A board that cannot answer these forces `None` through `mule/` permanently.
That is correct behaviour and a poor outcome.

**What it unblocks.** `TBR-RF-01`, `TBR-RF-02`, `TBR-RF-03`, `TBR-PWR-01`,
`TBR-THERM-01`, `TBR-LINUX-01`, `TBR-COMP-01`, `TBR-CARRIER-01`, `TBR-HW-01`.
Three of the four critical-path trades need it.

**Read first:** `docs/verification/FML-MULE-ITEP-v0.1.md` for which rig a result
needs, and `docs/evidence/README.md` for what counts as evidence. Rig R0 is the
only one needing no hardware and the only one that can produce no hardware
result.

**When hardware arrives, the first thing to do is not to build the product.** It
is to run the existing flat-sat scenarios against real interfaces and find out
which fakes were lying. `test/flatsat/README.md` names every fake with what it
does and does not simulate, and that list is the test plan for day one.

## Track 3 — analysis

### The blocker that gated everything, half cleared 2026-08-31

**Every trade now has a named owner: Cameron Zobrist.** Trades close on evidence
accepted by a named owner, so this removes the reason no trade could close.

**Owner assignment closed nothing by itself.** SAD section 30.2 says a TBR
closes when its listed evidence exists, the named owner accepts it, **and the
resulting architecture decision is entered into the ADR register**. As of
2026-09-06 four trades have met all three and are `CLOSED`: `TBR-NET-02`
(`FML-ADR-070`), `TBR-NET-01` (`FML-ADR-063`), `TBR-NET-03` (`FML-ADR-061`) and
`TBR-TAK-01` (`FML-ADR-071`, the one critical-path trade needing no hardware).
The rest remain `OPEN`, most gated on evidence that needs hardware, which is the
expected state at SRR.

**The SRR exit action is complete.** Section 30.2 asks for a named individual
*and a calendar target date* on every open TBR. The named individual was
assigned 2026-08-31, and on 2026-09-04 the Program Owner set the calendar target
date to **2026-09-30** across every open trade. For a hardware-gated trade that
date is a target the program drives toward, not a claim the capability exists by
then; setting it is the commitment SAD section 30.2 asks of the owner, which is
the owner's act to make rather than a specification this repository invented.

The four critical-path trades, for reference:

| Pri | Trade | Question | Hardware |
| ---: | --- | --- | --- |
| 1 | `TBR-PWR-01` | Endurance and battery mass | yes |
| 2 | `TBR-COMP-01` | CPU and memory budget | partly |
| 3 | `TBR-THERM-01` | Thermal architecture | yes |
| 9 | `TBR-TAK-01` | Mission-critical state boundary | no |

That assignment converted a register of permanently open questions into one
that can be worked. What each trade now needs is a **decision**, written as an
ADR, which is a different and larger piece of work than the evidence that
supports it.

### What SRR exit actually needs, and why closing trades is not it

Written 2026-08-31 after checking, because "close trades to reach SRR" is the
natural plan and the SAD does not support it.

**Trades are expected to be OPEN at SRR.** SAD section 30.2 states the exit
action in one sentence: *the Program Owner assigns one named individual and one
calendar target date to every **open** TBR.* Not one trade's closure gate falls
before SRR; every gate in the section 30.2 register is a later milestone --
"Before hardware PDR", "Before host selection", "Before ICD baseline". Closing a
trade early is not forbidden, it is simply not what this gate asks for, and most
of them cannot close before hardware exists anyway.

**Only two of section 30.1's twenty-one findings carry `SRR` as their stage.**

| Finding | State |
| --- | --- |
| TBR schedule concentration -- named-person assignment | **Done 2026-08-31.** Every trade names an owner. |
| Traceability integrity -- clause-complete section 35 | Not repository work. Section 35 is already clause-complete; it is `OPEN until formal RTM baseline`, and baselining an RTM is a program act. `docs/verification/requirements.md` records why this repository tracks the 33 section 79 criteria rather than duplicating a 140-row table. |

Everything else in that table is gated on CONOPS stages 1, 2, 5, 7, 8, 9 or 13,
which are test campaigns, and most need hardware.

### The remaining SRR item, target dates, is set

The Program Owner set every open trade's `target-date` to **2026-09-30** on
2026-09-04, performing the section 30.2 exit action. The reasoning below is why
that date is a *target* rather than a promise of capability, kept because it
still shapes what the date means and what would move it.

**Every closure gate is a milestone, and most milestones are hardware-gated.**
From the section 30.2 register: hardware PDR, host selection, hardware/enclosure
PDR, RF/BOM lock, HW/HA/security lock, hardware block lock, production software
PDR, HA architecture lock, PDR, RF design lock, CDR-lite, production image
baseline, Security Architecture lock, ICD baseline, production hardware-block
lock.

Section 30.2 recorded why the SAD itself left them undated: *No calendar schedule
has yet been baselined for FML/MULE. This SAD therefore does not invent dates.*
The Program Owner setting one blanket date is a different act from the SAD
inventing dates -- it is the owner's commitment, which section 30.2 explicitly
asks for -- and a baselined program schedule would still refine 2026-09-30 into
the per-milestone dates the hardware-gated trades really answer to.

### A risk this repository created on 2026-08-31

Section 30.1's own wording: *TBR schedule concentration -- named-person
assignment required at SRR; **owner concentration becomes program risk***.

All eighteen trades now name one person. That satisfies the first half of the
sentence and instantiates the second. The SAD anticipated it in the line that
asked for the assignment, and nothing has been done about it.

It is recorded rather than fixed because the fix is not a repository change:
either more people take trades, or the program accepts single-owner
concentration and says so. Both are the Program Owner's call. What must not
happen is the register reading as fully owned while the risk the same line names
goes unrecorded.

### `TBR-TAK-01`

The only critical-path trade needing no hardware. It gates the mission-critical
state boundary, and through it `services/mission-trust/` and
`services/status-aggregator/`.

**State, 2026-09-06: `CLOSED` on `FML-ADR-071` (`SELECTED`).** Fifteen evidence
artifacts exist, including a **running OpenTAKServer instance** with PyTAK
clients. The closure gate's classification half is met in full: all 41 tables
classified into CONOPS section 26 classes, the state outside the database
(`config.yml`, `ca/`, `uploads/`), and the map/tile/cache item (classified as
**not TAK-server state** -- OTS serves no tiles). Every empirical item is now
done: durable-queue inspection (no durable queue exists), the different-node
restore (restores every row, authenticates nobody, because the salt and CA live
in `OTS_DATA_FOLDER`), all four workflow tests (mission API, certificate,
mission-package, and DataSync content through `mission_content`), and the
partition/rejoin exercise -- which found reconciliation **structurally
impossible**, no OTS federation and no PostgreSQL replication, so the durable set
cannot converge and the only schema-supported merge is a wall clock the program
allows to be `TIME_DEGRADED`. **The decision is `FML-ADR-071`**, accepted by the
named owner 2026-09-06: the boundary is SQL plus the out-of-SQL durable set
(`config.yml`, `ca/`, `uploads/`), `TBR-HA-01` must carry both, and it must not
fix authority by comparing wall clocks. What follows is `TBR-HA-01` (the
mechanism) and the implementation, not more state study.

The implementation that follows is now **Track 4.1**, because running the server
established that the TAK service is three processes, not one.

**Read first:** the trade, `FML-ADR-049`, CONOPS section 26, and the seven
`TBR-TAK-01` artifacts. Several carry findings beyond the state study: a default
`administrator`/`password`, a certificate authenticated on a header with no proof
of possession, and no revocation path at all. Those are recorded for
`services/ingress/` and `THREAT_MODEL.md`.

**No longer deliberately-not-first.** It was held behind Track 1 while `os/` was
all `TBD`; that is no longer true, and the TAK work was done this session.

## Track 4 — the mission-service plane

**State:** blocked at the gate, by design. `services/catalog/` is empty because
no service is approved, and `services/quadlets/` holds no unit. Adding a service
is a decision with a record, not a file appearing in `quadlets/`. What this
track holds is the implementation work that becomes unblocked the moment a
service is selected, and what has already been learned about each from running
it on the bench.

The one piece of standing guidance: every service competes with the routing
daemon for one compute element (`FML-ADR-021`). The failure mode is specific and
`services/catalog/` names it -- a service takes memory, routing is starved, mesh
links flap, and the node looks like it has a radio fault when it has a scheduling
fault. `TBR-COMP-01` is where that is bounded.

### 4.1 The TAK service is three processes, not one

**CONOPS basis:** section 26 (TAK state classes), section 27 (TAK service
continuity), section 9 (service criticality). Decision: `FML-ADR-032`,
`FML-ADR-034`, `FML-ADR-035`, `FML-ADR-029`.

**State:** the state study is **done** (`TBR-TAK-01` is `CLOSED` on
`FML-ADR-071`) and the implementation is not started, but the shape is now known
from a running instance. `OpenTAKServer` is **three** console entry points, and
upstream's own container runs only the first:

- `opentakserver` -- the web application and API;
- `eud_handler` -- the CoT listener that binds the TCP/SSL/UDP streaming ports.
  **Without it the server accepts no TAK client at all;**
- `cot_parser` -- the worker that turns received CoT into rows.

**The implementation is therefore three Quadlet units, not one**, with a
dependency order (`eud_handler` and `cot_parser` need the database and broker;
all three share `OTS_DATA_FOLDER`), and `TBR-COMP-01` must budget three Python
processes. See `docs/evidence/TBR-TAK-01/2026-08-31-cot-end-to-end-with-pytak.md`.

**Read first:** `services/tak/README.md`, `services/quadlets/README.md`,
`FML-ADR-035` for service control, and the `TBR-TAK-01` artifacts, which
record what state each process holds and what a restore does and does not carry.

**The constraint people miss:** the durable set is not all in the database. A
failover that copies only the database restores every row and authenticates
nobody, because the password salt and the certificate authority live in
`OTS_DATA_FOLDER`. Any service definition that ignores the data folder produces a
node that looks healthy and works for no one. See
`2026-08-31-different-node-restore.md`.

**Done when:** three Quadlet units exist, are catalog entries with their images
pinned by digest (`FML-ADR-029`), start in a defensible order, and a
different-node restore that carries the data folder produces a working
replacement. Gated on `TBR-TAK-01` acceptance and a catalog decision.

### 4.2 The RF voice gateway (RoIP)

**CONOPS basis:** section 45 (external VHF/UHF/HF integration), section 5
(familiar-interface and local-first principles), section 40 (traffic
preference), section 41 (WAN independence). Decision: `FML-ADR-064` through
`FML-ADR-067`, all `SELECTED` under `CCR-03`.

**State:** `CCR-03` is approved (2026-09-15) and the four voice ADRs are
`SELECTED`. The capability is a CONOPS v1.1 increment whose text reissue is the
pending baselining step (section 86 stakeholder re-approval); nothing here is
built yet, and it remains a v1.1 capability, out of v1.0. The decisions: DM-32UV
as the radio (`FML-ADR-064`), audio/PTT over IP not native DMR (`FML-ADR-065`), a
dedicated integrated gateway radio (`FML-ADR-066`), and the single-audio-egress
invariant (`FML-ADR-067`). With `CCR-03` approved, the `TBR-VOICE-01` gateway
analysis half is now produced
(`docs/evidence/TBR-VOICE-01/2026-09-15-gateway-candidates-analysis.md`): it
narrows the candidates on the no-hardware `CCR-03` section 11 criteria and the
`FML-ADR-067` enforceability question, and selects nothing -- the measured
RAM/CPU/latency and the owner's acceptance are the hardware half (GATE VOICE-01).

**The baseline requirement to carry through implementation:** an operator's
headset receives a linked voice session through **exactly one path**
(`FML-ADR-067`). In v1 that path is always the operator's own radio over local
RF. The software must guarantee no second copy arrives -- no direct
MULE-to-headset audio, self-echo suppression by origin/session ID, and a single
active gateway per voice group per local net. A voice baseline that can put two
copies in one ear is not acceptable, which is why this is an invariant and not a
tuning goal.

**Read first:** `docs/change-requests/CCR-03-integrated-rf-dm32-roip-voice.md`,
the four ADRs, `TBR-VOICE-01` for the implementation trade, and
`hardware/prototype/BOM-v0.4-DM32-RoIP-handoff.README.md` for the hardware and
its gates.

**The constraint people miss:** the gateway is a service like any other. It
needs a catalog entry, a Quadlet, and `TBR-VOICE-01` selected before it runs,
and it adds a worst-case contributor to `TBR-COMP-01`. Its QoS demand competes
with the routing daemon this track's standing guidance warns about.

**Done when:** `CCR-03` is approved, `TBR-VOICE-01` selects an implementation,
and the gateway runs as a catalog service meeting `FML-ADR-067`'s invariant,
verified at the BOM's GATE VOICE-06. Everything before that is blocked on the
change request.

### 4.3 The unknowns to resolve before RoIP can be scheduled

**State:** open questions, recorded so they become roadmap items rather than
surprises. Each needs work before 4.2 can be planned in detail.

- **RX activity detection** (`CCR-03` section 10.3, CONOPS 45): hardware COS/COR
  versus validated squelch. The handoff warns not to assume audio-energy or VOX
  detection is adequate. This is a hardware-interface unknown and gates reliable
  PTT arbitration.
- **RF coexistence** (`TBR-RF-02`, `FML-ADR-027`, CONOPS 45): a transmitting
  gateway radio inside the enclosure with HaLow and LoRa in the same band.
  Measured at the BOM's GATE VOICE-01 and VOICE-09; nothing on the bench can
  answer it.
- **Compute under a live session** (`TBR-COMP-01`, CONOPS 9): whether the 4 GB
  CM4 holds the full service-host load plus an active RoIP session. The BOM
  makes this a gate with an explicit fail-back to 8 GB.
- **Voice-group authorization distinct from reachability** (`FML-ADR-061`,
  CONOPS 43, 44): being on the mesh must not be being in the voice group. Same
  shape as the keyed-mesh admission finding, and it needs the credential
  distribution that `TBR-SEC-01` records as absent. Now tracked as
  **`TBR-VOICE-02`** (depends on `TBR-SEC-01` and `TBR-VOICE-01`), so it is a
  trade rather than a loose unknown.

The transport half of two of these -- the latency of multiple mesh hops, and
voice-versus-data contention on one bearer -- is now measured on the bench,
`SIMULATED`, in `docs/evidence/TBR-RF-01/2026-09-14-mesh-multihop-latency-hwsim.md`
and `docs/evidence/TBR-RF-01/2026-09-14-voice-data-contention-hwsim.md`. What
those cannot reach is the mouth-to-ear half: the audio pipeline (DigiRig, radio,
Opus) is unbuilt, so it waits on `TBR-VOICE-01`.

### 4.4 A local map service

**CONOPS basis:** section 9.2 (S1 local mission services -- "selected cached
maps"), and the high-rate bearer's "map packages" purpose. Decision: `FML-ADR-073`
(`SELECTED`) selects the store and server; the selection is `TBR-MAP-01` and the
service outline is `services/map/README.md`.

**State:** a gap, surfaced 2026-08-31 by the question "why can't we have map
cache". Two things were being conflated. **Device-side tile caching** is an ATAK
client function -- the client caches tiles it renders -- and is what
`TBR-TAK-01`'s cache question (item 6) was about. That item is now **resolved by
classification**: map/tile/cache is not TAK-server state (OTS serves no tiles),
so it is the EUD's own 26.3 cache and this S1 service, not TAK state
(`docs/evidence/TBR-TAK-01/2026-09-05-map-tile-cache-state-classification.md`).
**Serving maps locally** is a different thing: not a TAK-server
function at all (OpenTAKServer handles no tiles), not ATAK-only, and per CONOPS
section 9.2 a **MULE S1 service**. The TAK server is S2. So maps sit in a
*higher* availability tier than TAK and are supposed to remain when TAK is gone.
Since 2026-09-04 the capability has three results under
`docs/evidence/TBR-MAP-01/`: the committed **interface** exercised (`SIMULATED` --
an `MBTiles` store served over `z/x/y` with an iTAK map-source definition,
prompted by "does OTS feed maps to iTAK offline" -- it does not; OTS serves no
tiles, so this service is the only offline basemap path); a **real iTAK EUD
rendering a high-detail map** streamed from the node with WAN cut (2026-09-04),
which settles the interface and client model and meets the EUD-render
acceptance; and the **map-server-for-the-mesh role** -- a storage-less node
fetching a repository tile from a storage node across `batman-adv`,
byte-identical to the store's copy (`SIMULATED`, 2026-09-05,
`test/bench/map-server-mesh.sh`). The **production server is now selected and
sized** (2026-09-06): Martin (MapLibre), a rootless, digest-pinned, single-binary
MBTiles-to-`z/x/y` server, chosen over `mbtileserver` (no arm64 image) and
`tileserver-gl-light` (a GL renderer, a v1 non-goal), with a measured software-half
envelope of idle ~8.5 MB / peak ~28 MB RSS
(`test/bench/map-server-footprint.sh`,
`docs/evidence/TBR-MAP-01/2026-09-06-martin-mbtiles-server-footprint.md`). What
remains for closure is the hardware and content basis, not the interface or the
server: no CM4 footprint (`TBR-COMP-01`), and no store size from real imagery on a
permitted source with the `TBR-SEC-01` call and a USB2 read-latency check. The
2026-09-04 session also found the store cannot come from OSM's public tiles (a
permitted source is required) and that clients cache tiles by position, not by
source.

**What it is:** a local tile/map source on the node -- offline tiles, an MBTiles
store, or a WMTS/XYZ endpoint -- so EUDs render maps with no internet and no
reachable external tile server. It is a service-plane capability distinct from
the TAK service, and nothing in `services/` provides it.

**Read first:** `services/map/README.md`, the service outline, which commits to
one interface -- a `z/x/y` tile endpoint and an ATAK map-source definition --
and leaves the mechanism to `TBR-MAP-01`. Then CONOPS section 9.2 for the S1
tier, `services/catalog/` for the gate every service passes, and
`docs/NON-GOALS.md` to confirm map serving is required as an S1 example rather
than excluded.

**The constraint people miss:** this is S1, above the TAK server, so it must run
locally on the node under the same one-compute-element budget (`FML-ADR-021`,
`TBR-COMP-01`) and the same catalog and Quadlet gates. A tile store is also
storage, which bears on the pack and on `TBR-SEC-01`'s at-rest posture if the
imagery is sensitive.

**Done when:** `TBR-MAP-01` selects a tile store and server, a catalog entry
and Quadlet exist for it with the image pinned by digest, and an EUD renders a
map from the node with no external network. No hardware to start the selection;
the field demo needs a device.

### 4.5 Time credibility without GPS or NTP

**CONOPS basis:** sections 26, 27 (mission-critical state continuity). A
WAN-independent node still issues TAK timestamps and validates certificate
windows; both rest on the clock being trustworthy, and `FML-ADR-042` decides
that credential validity never fails open on a doubtful clock.

**State:** the per-node half is built and the merge half is analysed; the values
are the open trade. `mule/timekeeping.py:assess` decides credibility fail-closed
(`FML-ADR-042`), with two consumers already refusing on `TIME_DEGRADED`
(`mule/admission.py`, `mule/status.py`). The readings exist in `mule/sysfs.py`,
and the `synchronized` reader (`parse_chronyc_tracking` + an injectable
`chronyc` probe) was added 2026-09-14, closing the last `NO READER` cell in the
`docs/readings.md` Time table. The partition/rejoin reconciliation rule -- what
happens to two clocks when `FML-ADR-061` merges two deployments -- is analysed in
`docs/evidence/TBR-TIME-01/2026-09-14-partition-rejoin-time-reconciliation.md`,
which leans v1 toward adopting no peer time (the credential to authenticate a
time source is the `TBR-SEC-01` gap). What remains needs hardware or an owner:
the drift, holdover and skew-window **values** (`TBR-TIME-01`, needs a candidate
RTC over a temperature interval -- Track 2 day-one), the RTC battery-low flag as
a board selection criterion (`TBR-HW-01`, `docs/readings.md` records it may have
no signal at all), and, only if the trade chooses authenticated peer time, the
credential from `TBR-SEC-01`.

**GNSS is optional, and not required per node.** The network's position picture
comes from the EUDs, not the MULE: each ATAK/iTAK client self-reports position as
PLI CoT from its own receiver, which needs no WAN and rides the local mesh to OTS
and the other clients (CONOPS PLI). GNSS on a MULE therefore serves only time
discipline, and `FML-ADR-042` with SAD section 24.5.1 make it optional -- "GNSS
is optional mission hardware, not a prerequisite for baseline boot"; baseline time
is the battery-backed RTC and chrony, disciplined opportunistically by GNSS or WAN
when present and failing closed otherwise. Because the partition/rejoin analysis
leans v1 toward adopting no peer time, this does not rest on a node borrowing time
over the mesh: a node without GNSS relies on RTC holdover (values open in
`TBR-TIME-01`) and fails closed rather than trust a doubtful clock, and it never
takes its security-relevant time from an admitted EUD.

**Done when:** `TBR-TIME-01` sets the skew and holdover values on measured RTC
drift, its named owner accepts them, and the partition rule is selected (peer
time adopted, or not) and entered in the register.

### 4.6 Browser-service identity and admission

**CONOPS basis:** section 9 (the mission-service plane and its access control),
and the browser-service authorization that `4.1` (the TAK service) and
`services/ingress/`'s `X-Ssl-Cert` work depend on. This is the coverage-map gap
that read "identity needs its own item under Track 4."

**State:** hardware-free design work, ready now. `TBR-ID-01`
(`requires-hardware: no`) asks whether the browser services need a common
identity provider; its workflow analysis -- count authentication events with and
without one -- is already scoped in ITEP-C01 and needs no node. The decisions are
`FML-ADR-037` (application-native RBAC first, OPA only when cross-application
policy justifies it) and `FML-ADR-036` (step-ca as the preferred PKI). The
admission decision logic exists in `mule/admission.py` but today gates only on
time (`TIME_DEGRADED`); it does **not** yet check an identity, which is the visible
gap. `TBR-ID-01` `depends-on TBR-TIME-01` because a certificate window is only
meaningful against a trustworthy clock -- and that dependency is on the time
*credibility* logic (`4.5`, built), not the hardware *values*, so it does not
hold identity design back.

What is in this item: the identity-provider decision (`TBR-ID-01`), the RBAC
model (`FML-ADR-037`), and extending the admission decision function to reason
about identity, not only time -- a pure `mule/` function under `FML-ADR-052`.
What is **not**: building the blocked `services/mission-trust/`, and the
credential *at rest*, which is `TBR-SEC-01`'s hardware half.

**The wider admission and enrollment picture (recorded, not yet decided):** this
item is the service-identity half of a larger network-admission layer that has
no roadmap home of its own, recorded here in the style of `4.3` so it does not
drift. The settled anchors, with their real status:

- The network-admission target is EAP-TLS (`FML-ADR-038`, `SELECTED TARGET`): a
  per-device, revocable, time-bounded credential, with a MAC address or a shared
  WLAN password explicitly **not** sufficient. It is a *target* -- not
  demonstrated on the selected hardware -- and per-device PPSK is a sanctioned
  prototype path, so "a certificate to join, no password" describes the goal,
  not today's bench.
- The PKI shape is `FML-ADR-036` (`PREFERRED`): an offline root that stays
  offline and is never required on a MULE, mission intermediates delegated to
  field nodes, and **short-lived credentials as the primary revocation
  mechanism** -- the ADR names no lifetime value and no renewal mechanism.
- Trust is distributed per MULE and admission works **offline**, but revocation
  **lags and is partition-blind** (`FML-ADR-047`); admission depends on credible
  time and fails closed (`FML-ADR-042`).
- Identity is separate from authorization (`FML-ADR-037`): the certificate
  proves identity, while role and organizational scope are carried in signed
  mission policy and should **not** be baked into a long-lived device
  certificate.

**Proposed directions (they feed `TBR-ID-01`, some exceed its scope, and none is
decided):**

- A **single deployment identity**, so one enrollment reaches every service by
  name through ingress (`FML-ADR-031`). This needs a **common deployment CA**,
  which cuts against the shipped OpenTAKServer default of a CA regenerated per
  node (`FML-ADR-071`); and ingress already records that a TLS certificate a
  browser accepts, offline, is genuinely unsolved.
- A **constrained onboarding SSID** as the primary path to issue and reissue a
  certificate -- the piece that resolves the bootstrap deadlock a cert-to-join
  network creates (a device with no valid certificate cannot reach enrollment),
  which `FML-ADR-038` does not address. It would be firewalled to the enrollment
  endpoint only, and evil-twin-defended by shipping the CA pin in the per-user
  profile so a rogue look-alike onboarding access point cannot harvest
  credentials.
- A **short certificate lifetime (on the order of a week) with silent
  auto-renewal on connectivity, and revocation by non-renewal**. No ADR sets a
  lifetime or a renewal mechanism today, and the direction fights the shipped
  OpenTAKServer default of ten-year certificates. The lifetime is the tunable
  knob: it is both the revocation window and the longest partition a legitimate
  node can survive before it expires, and a short lifetime deepens the dependence
  on credible time (`FML-ADR-042`).
- Package and QR onboarding: a cross-platform data package imported into ATAK
  for the service identity, an iOS configuration profile for the EAP-TLS Wi-Fi
  certificate (Android has no equally clean single-file path), and one-time
  per-user enrollment tokens in preference to reusable passwords.

**Residual risks and open sub-decisions (documented, not solved):**

- **Physical capture is an expected condition and yields keys.** `THREAT_MODEL.md`
  records no secure element and no tamper response, and that a node captured
  while running is captured unlocked; zeroize is a cryptographic erase only and
  data survives it physically (`FML-ADR-044`); LUKS protects a powered-off node
  only (`FML-ADR-043`). So an issuing key in the field cannot be protected by
  secrecy -- only by scoping it to one deployment, keeping it short-lived, and
  revoking it, with the organizational root kept offline (`FML-ADR-036`).
- **The mesh credential is coarse and un-rotatable.** Mesh membership is one
  shared SAE credential, a captured node yields it, rekeying has no mechanism,
  and the result is `SIMULATED` only (`FML-ADR-061`). This is a different, lower
  layer than per-device EUD admission and is not fixed by it.
- **Revocation is weak in the shipped stack.** OpenTAKServer certificates default
  to ten years and its Marti API certificate path checks the chain but not
  private-key possession and consults no revocation (`THREAT_MODEL.md`);
  `FML-ADR-047` cannot bound the lag. Short-lived, renewal-gated credentials are
  the mitigation, but they are a direction, not a built control.
- **Single-identity reach is a single blast radius.** One credential reaching
  every service argues for least-privilege RBAC (`FML-ADR-037`) and for hardening
  any configuration-capable identity separately from an ordinary read-only one.
- Open sub-decisions, named so they do not surprise later (no identifiers minted
  here): where renewal and issuance are served (a central authority versus every
  MULE -- the partition-resilience against issuing-key-exposure trade); whether
  the onboarding SSID is adopted at all, and its scope and bootstrap rules; and a
  mesh-key rotation mechanism to close the gap `FML-ADR-061` leaves open. The
  nearest existing home is `TBR-ID-01`; the network-admission pieces exceed its
  current workflow-analysis scope.

**Done when:** `TBR-ID-01`'s workflow analysis decides whether a common identity
provider is warranted, its named owner accepts it, and the admission model
incorporates identity alongside time, with the decision entered in the register.

### 4.7 The operator status view

**CONOPS basis:** section 67 (the simplified operator view -- "is the MULE
working?", without making an operator read BATMAN tables) and section 65 (the
EMCON confirmation path). The component is `FML-ADR-046` (approved thin original
software), with the Service Authority Registry folded in by `FML-ADR-049`.

**State:** the hard dependency closed, so the roll-up is a buildable P1 bench
increment. `services/status-aggregator/README.md` named `TBR-TAK-01` its hard
dependency; that closed 2026-09-06 (`FML-ADR-071`), defining the mission-state
data model, so the "inventing a state taxonomy" hazard is retired for the
reasoning spine (`mule/status.py:derive`, `mule/modes.py`, already exercised, a
pure function under `FML-ADR-052`). A bench increment -- assemble `Observations`
from the existing readers, serve `NodeStatus` as JSON over loopback, show the
live mesh link -- is demonstrated in
`docs/evidence/status-view/2026-09-15-operator-view-over-mesh-hwsim.md`
(`test/bench/operator-view.py`, `operator-view.sh`), verified against the README's
gate by an independent agent 2026-09-14. That bench now also derives a per-peer
capability tier (`FML-ADR-080`) from the passive signals, as bench telemetry
alongside the mesh-link counts and demonstrated in
`docs/evidence/status-view/2026-09-18-per-peer-capability-tier-over-mesh-hwsim.md`.
That tier is keyed by peer MAC; making it operator-meaningful needs the
MAC-to-callsign mapping (`FML-ADR-070`'s `Contact.callsign` and the roster) that
item `4.6` owns -- an unwired dependency of this view, not just of admission.
What stays out: the Service Authority
Registry and the `shared_data_authoritative`/`data_stale` fields (`TBR-HA-01`), a
fielded daemon's resource envelope (`TBR-COMP-01`), a **production** mesh-links
reader (parked on `TBR-RF-01`/`TBR-RF-03`/`TBR-LINUX-01`, so live mesh links are a
bench readout only), and the I2C display (hardware).

**The operator-facing view (recorded design; a `SIMULATED` mock, nothing
fielded):** the State above is the roll-up's data spine; this is what an operator
sees on top of it. One standard dashboard serves every organization -- there is
no per-deployment "operational profile" to configure, because the roster supplies
the labels, the vitals are the universal union, and a field that does not apply to
an org is ignored after a brief rather than switched off. The view is
capability-first: it answers what a link can carry -- video, voice, or text
(the tiers named by `FML-ADR-080`) -- rather than a raw or fabricated rate, and
that tier comes from the passive floor and the paced probe of item `1.9`, never
from a number the mesh cannot substantiate. It is glanceable -- complete
node-and-network status in about five seconds, without scrolling, on a phone, in
both portrait and landscape (many EUDs are vehicle-mounted) -- minimalist and
low-light, in plain operator language
(emission, runtime, direct or via a relay, IP or LoRa), and it distinguishes the
IP plane from the LoRa (Meshtastic) plane (`FML-ADR-026`). It is served over HTTPS
because call signs are OPSEC-sensitive, read-only for most, with configuration
(EMCON, bearer power, EUD boot) gated to authenticated roles on the same identity
model as `4.6`.

**The three behaviours the fielded view must add:**

- A node reporting `OPERATIONAL` while a peer is unreachable **shall not** read as
  all-clear: the view **shall** carry the reachable count and mark the loss, and
  **shall** alarm a *recent* loss rather than dim it, dimming only a long-stale
  peer.
- The state word **shall** demote from `OPERATIONAL` to `DEGRADED` on a defined
  trigger -- loss of the WAN reach-back (`FML-ADR-069`) or loss of the last path
  to a pinned peer -- so a green header cannot mask a backhaul or reach loss, and
  a WAN loss **shall** alarm with parity to a down node rather than change one
  quiet field.
- A daylight, high-contrast variant **shall** exist: the near-black low-light
  palette that suits a vehicle cabin at night washes out on a handheld in direct
  sun. The browser-free EMCON confirmation path remains the I2C OLED of
  `FML-ADR-046` (section 65), not this view.

**Done when:** `TBR-HA-01` closes so the authority fields can be answered,
`TBR-COMP-01` sizes the daemon, and the aggregator runs as a catalog service
meeting `FML-ADR-046`/`FML-ADR-049` with the operator states of SAD section 22,
and the fielded view meets the three behaviours above.

### 4.8 EUD-native voice and video

**CONOPS basis:** section 9.2 (peer-to-peer ATAK as a local mission service that
survives when external hosts are gone) and the non-radio user it implies -- a
civilian response unit on an everyday phone with no DM-32. It extends the RoIP
flow of `4.2`/`4.3` and feeds the capability display of `4.7`.

**State:** post-v1, nothing built, recorded so it does not drift or get conflated
with the approved RoIP work. RoIP (`4.2`, `CCR-03` approved, `FML-ADR-064` through
`FML-ADR-067`) is external-radio voice -- it bridges a DM-32 handheld onto the IP
bus. This item is the other half: voice and video for an EUD user who carries no
radio, which `FML-ADR-067` explicitly places outside the v1 baseline
(direct-to-headset and non-radio audio, and dual-comm, are out). So it is a later
increment than the v1.1 RoIP, not a deferral of it.

**The shape (recorded, not decided):**

- Voice rides the IP mesh, EUD-agnostic, through a MULE-served web application and
  WebRTC -- the browser supplies the microphone, the Opus codec, the jitter buffer
  and the mix, and a flat layer-2 subnet removes the usual NAT traversal. The
  baseline groups are small (a squad net, direct calls, a team-leads net, a TOC
  net) and ride full-mesh with no server-side mixer; a federated selective-
  forwarding unit is a growth rung for a large single net, gated on measured need.
  The media service uses the IP plane and, per `FML-ADR-028`, never owns network
  or RF state.
- Video is a separate plane and is not this item's to build: it rides the TAK
  video path (OpenTAKServer plus a media server, endpoint-encoded, served as
  RTSP/HLS/WebRTC) on the high-rate bearer (`FML-ADR-025`) with QoS, not the voice
  path. That media server is not yet a catalog entry, so adding it is future
  `FML-ADR-078` catalog work.

**Read first:** `docs/architecture/roip-voice-data-flow.md` (the RoIP flow this
extends), items `4.2` and `4.3`, and `test/bench/mesh-traffic.sh` for the
transport-viability measurement.

**Done when:** the transport is shown to carry voice-grade multi-hop traffic under
contention on real hardware (`TBR-RF-01`, advanced by `test/bench/mesh-traffic.sh`
today), `TBR-VOICE-02` selects the voice-group authorization model and its merge
behaviour, `TBR-COMP-01` sizes any node-side media component, and a scope decision
brings EUD-native voice into a version -- with the decision entered in the
register. It stays out of `v1.0`, and later than the v1.1 RoIP, until then.

## Before the BOM: what to bank on current hardware

**The goal, stated by the Program Owner 2026-09-05:** get the program to a full
system readiness review and begin prototype creation, and use the current bench
to de-risk as much as possible **before any prototype material is ordered**, so
the BOM is chosen on evidence and the first build is integration rather than
discovery.

This is a *different* question from the SRR exit action, which is already met
(named owners and a target date on every open trade -- see "What SRR exit
actually needs" above; trades are expected `OPEN` at SRR and closing them is not
what the gate asks). SRR readiness is a governance state. This section is the
engineering state that makes the prototype worth building: the work that is
free now and expensive to discover after the boards are on the bench.

**"Current hardware" is not "no hardware."** The bench today is an x86 dev host,
`mac80211_hwsim`, one real AP-capable USB radio (RTL8812AU, no mesh mode), the
onboard CYW43455, the full OpenTAKServer container stack, and a real iTAK EUD.
That is rig R0 plus a real access point and a real client -- enough to exercise
every plane except the physical ones (`TBR-RF-*`, `TBR-PWR-01`, `TBR-THERM-01`),
which need the BOM and are Track 2's day-one work. Nothing below waits on a
purchase.

The work sorts into three buckets by what it produces.

### Bank A -- what can actually close now (software only, plus the owner's act)

These need no hardware. Each needs its evidence finished and then the owner's
acceptance and an ADR -- the governance half, not more engineering.

- **`TBR-TAK-01`, the mission-critical state boundary (Track 3, `4.1`) -- now
  `CLOSED`.** The one critical-path trade needing no hardware is closed on
  `FML-ADR-071` (2026-09-06): fifteen artifacts, a running OTS instance, every
  empirical and classification item done, the owner's acceptance recorded. It
  gated `services/mission-trust/`, `services/status-aggregator/` and
  `services/gateways/`; what unblocks them next is `TBR-HA-01` (the mechanism the
  boundary constrains) and a catalog decision, not more state study.
- **The GeoChat.to survival probe -- done 2026-09-06.** `FML-ADR-070`'s encoding,
  `Contact.callsign` and `GeoChat.to` in a `TAKPacket`, crossed two `meshtasticd`
  nodes with both fields intact (`test/bench/geochat-survival.sh`,
  `docs/evidence/TBR-NET-02/2026-09-06-geochat-to-survives-the-meshtastic-bearer.md`).
  The custom-tag falsifier was moot; this verified the *selected* encoding on the
  bearer, on upstream's own ATAK port.
- **`4.1`, the TAK service as three Quadlet units.** Buildable now against the
  bench containers: the three catalog entries with images pinned by digest, a
  defensible start order, and a different-node restore that carries
  `OTS_DATA_FOLDER`. Gated only on the `TBR-TAK-01` acceptance above and a
  catalog decision, both the owner's.

### Bank B -- what to mature now to "only a hardware measurement remains"

These stay `OPEN` because their closure gate has a hardware item, but their
software half is bankable now, so the day the BOM arrives the trade is a
measurement rather than a design.

- **`TBR-COMP-01`, the service-plane budget.** Marked `requires-hardware: partly`
  precisely because half is not. The **size half is now banked** (2026-09-06): the
  service plane sizes at **~650 MB resident** at idle steady state, dominated by
  OpenTAKServer's three processes (~536 MB) and RabbitMQ (~98 MB), measured from
  the running reference deployment (`test/bench/service-plane-footprint.sh`,
  `docs/evidence/TBR-COMP-01/2026-09-06-service-plane-steady-state-footprint.md`).
  That is the input the CM4 memory-class call (Bank C) is made against. What
  remains is the hardware half: the arm64/CM4 figure, CPU under load, and the
  **peak** under start-up, mesh reconfiguration and an association storm with the
  network plane co-resident -- which need radios.

  The **prototype/test compute is the Raspberry Pi 4B (8GB)** -- a `TBR-COMP-01`
  working article, not a trade closure. It shares the CM4's BCM2711 SoC, so the
  arm64 CPU/RAM figures it produces transfer to the memory-class call. Its **core
  configuration** is onboard Wi-Fi as the EUD AP, HaLow (WM1302 HAT over SPI) as
  the long-range backbone, and LoRa over USB; the `FML-ADR-025` **high-rate 5 GHz
  plane is deferred**, because the Pi 4B exposes no PCIe for the QCA6174 and its
  only high-rate path is a USB3 mt76 adapter -- a stand-in, not the BOM radio.
  This does not close `TBR-COMP-01` (which closes on the peak/under-load figures
  above, with an owner), and the **CM4/CM5 stays the field-article candidate** for
  the M.2/PCIe, eMMC and sealed-carrier integration a Pi 4B SBC cannot provide.
  The BOM NODE-CORE compute row is unchanged.
- **`TBR-MAP-01`, the tile store and server (`4.4`).** The interface, the client
  model, the EUD render and the map-server-for-the-mesh role are all
  demonstrated (see `4.4`). The store format (`FML-ADR-073`, per-mission MBTiles)
  and the production server (Martin, selected and sized software-half, 2026-09-06)
  are now **made** on the bench; only the CM4 footprint and the real-imagery store
  size (with the USB2 read-latency check) remain, and neither blocks the now-
  buildable catalog entry and Quadlet.
- **Interface bring-up and `RadioState` (`1.2`, `1.6`).** The bring-up ordering
  and the `RadioState` reader are software, exercisable on `hwsim` plus the real
  AP radio. Finishing them means that the day a board arrives, bring-up follows a
  known sequence instead of being an experiment, and Track 2 day one is running
  the flat-sat against real interfaces to find which fakes were lying.
- **The rest of the `batman-adv` and 802.11s template (`1.7`).** Decide the mesh
  configuration in the template before radios exist, so the mesh is a
  known-good config on the prototype rather than a variable.

### Bank C -- the decisions that choose the BOM (make them before the purchase)

These are the trades whose answers *determine what to order*. Making them after
the purchase is how the wrong parts get bought. None needs the prototype; each
has bench evidence already or needs only the owner's direction.

- **`TBR-RF-03`, AP and mesh radio consolidation.** The one-radio AP-plus-mesh
  concurrency has a `SIMULATED` bench
  (`docs/evidence/TBR-RF-03/2026-09-04-one-radio-ap-plus-mesh-hwsim.md`). The
  *direction* -- consolidate onto one mesh-capable radio, or keep AP and mesh on
  separate boards -- sets how many Wi-Fi boards the BOM carries and whether the
  single M.2 slot is freed. It is the hinge the other two hardware decisions turn
  on.
- **`TBR-CARRIER-01`, the M.2 slot: radio or storage.** Decides whether the
  prototype carries a `>=256 GB SSD` for the map and service repository -- the
  M.2-baseline-capability direction the owner set (a node must have the option
  and the path to a large map repository that serves clients and the mesh).
  Depends on `TBR-RF-03` freeing the slot.
- **`TBR-COMP-01`'s hardware axes: memory class and storage.** The 4 GB versus
  8 GB CM4 fail-back (the RoIP gate in `4.3`) and the storage class and bus. The
  Bank B software-size measurement now informs the memory call directly: the
  service plane is ~650 MB resident at idle (see Bank B), so the call is between
  that plus the network-plane reserve, the OS and headroom against 4 GB, versus
  the room 8 GB gives -- a decision for the owner with the power model, not made
  here.
- **The deployment and portability model (two tiers, one hardware-agnostic
  stack).** The software targets the **CM4 carry node** (battery, sealed, passive
  cooling, 4 GB core profile) as the reference article, but is designed to deploy
  **unchanged to any capable Debian host** -- a mains/vehicle-powered COTS mini PC
  or desktop as a **TOC node** running the media profile (SFU voice, multi-stream
  video, RoIP, WAN hub, longer retention, and a natural home for the PKI root).
  This consolidates decisions already made, not new architecture: one Debian host
  (`FML-ADR-021`), node logic in an importable package outside the test tree
  (`FML-ADR-051`), mission services that never own the RF/network (`FML-ADR-028`),
  radio access behind narrow interfaces with fakes (the `T | None` reading
  discipline), per-bearer capability as a named tier (`FML-ADR-080`), and
  upstream-first gateways for new mediums (`FML-ADR-048`). The stack is therefore
  designed to be **RF-agnostic** -- driving whatever bearers are present through
  those interfaces (HaLow, 802.11s high-rate Wi-Fi, LoRa/Meshtastic as each is
  integrated on hardware) and extensible to new mediums/waveforms via the same
  interface and gateway pattern, bounded by the host's I/O and available drivers,
  not by the core. Because the baseline is a distributed full-mesh element, the
  **TOC is additive, not a single point of failure**: if it drops, the carry fleet
  keeps SA, voice and the mesh and loses only the heavy convergence. The
  prerequisites not yet built are **multi-arch images** (every OCI image for arm64
  *and* amd64, by digest) and a carry-versus-TOC **service profile** in the
  catalog; both extend what exists rather than redesign it. The N150 dev host
  already runs the stack on amd64 (the Bank B ~650 MB measurement was taken there),
  so the TOC tier is partly demonstrated; the carry tier and the multi-arch build
  are the open work. A third, lower tier follows from the same agnosticism: a
  **bring-your-own / expedient node** -- an existing laptop, mini PC or Pi plus USB
  bearers (USB HaLow, USB LoRa/Meshtastic, an mt76 USB Wi-Fi, onboard Wi-Fi for the
  AP) running the same stack at the cost of the radios alone. It is the open-source,
  low-barrier entry path that fits the disaster-response mission; the curated Debian
  image (`FML-ADR-040`) is what makes it turnkey rather than a per-kernel
  HaLow-driver gamble (`TBR-LINUX-01`), and an installer for an existing Debian host
  remains the distribution step for that path. It is an expedient node, not a sealed
  field article, and the deployer owns regulatory compliance (`REGULATORY.md`).
- **The prototype BOM itself (`hardware/prototype/`).** Once RF-03, CARRIER-01
  and the COMP-01 software budget are set, the BOM's open cells -- a committed
  SSD, the Wi-Fi board count -- resolve, and the purchase is made against a
  de-risked design.

**What this buys.** When the BOM is ordered, the network plane, the TAK service,
the map service and the compute budget are already exercised end to end against
fakes and one real EUD; the services that were placeholders have interfaces; and
the hardware trades are measurements with a known method (`test/bench/` and the
ITEP's rigs), not open designs. The prototype build becomes integration plus the
physical measurements only hardware can settle -- `TBR-RF-*`, `TBR-PWR-01`,
`TBR-THERM-01` -- which is the smallest, cheapest first build the evidence
allows.

## Sequencing

**Where the state lives, because this section kept going stale.** Each item
below carries a `**State:**` line, and that line is the only place its state is
written. This section holds the *reasoning* about order, which does not change
when something is finished.

It used to hold both. Finishing one item then invalidated three paragraphs
here as well as the item's own line, and the file was corrected three times in
two days, each time for the same reason. If you finish something, edit its
`State:` line. Nothing in this section should need touching.

A machine checks half of that: `tools/validate-docs.sh` fails if a numbered
item has no `State:` line, so the single source cannot quietly go missing. It
cannot check the other half. Nothing detects state creeping back into the prose
here, and the only thing preventing it is whoever is reading a diff.

### What to work, in general

Work the numbered items in Track 1 in order, skipping any whose `State:` line
says it is waiting on something. Track 2 starts the day hardware arrives and
takes precedence over everything, because it converts assumptions into
measurements. Track 3's blocker item is the Program Owner's and costs five
minutes; `TBR-TAK-01` is now `CLOSED` on `FML-ADR-071`. Track 4 is blocked at the catalog gate for the
services and on `CCR-03` for voice, but its analysis, the TAK state study, is
done.

An item's number is its dependency position, not a queue ticket. Two items with
nothing between them can be worked at once.

### Why the order is this order

This is the durable part, and it changes only if a dependency changes.

- **1.1 before 1.2**, because the second waveform is the largest unknown and
  delaying it repeats how the first one went.
- **1.2 before 1.6**, because reading radio state is worth little before
  something brings radios up in a known order.
- **1.5 threads through all of them** and can be worked in parallel by someone
  else, because an addressing plan constrains the others without depending on
  them.
- **The gateway tag probe is on no numbered item**, because it is not
  sequencing work. It is described below and can be taken at any time.

### The GeoChat.to survival probe

The original falsifier here was a **custom** one-byte member index in the
payload. It is answered and moot: the Program Owner chose upstream's own
`Contact.callsign` and `GeoChat.to` instead (`FML-ADR-070`), and `TBR-NET-02` is
`CLOSED`. `docs/evidence/TBR-NET-02/2026-08-30-opentakserver-meshtastic-path.md`
found a custom tag on a private port is discarded by the `FML-ADR-048` gateway,
which is exactly why the program pivoted to the fields the ATAK plugin protobuf
already carries.

What is still worth exercising is whether `FML-ADR-070`'s chosen encoding
survives the **bearer** end to end: a `TAKPacket` carrying `Contact.callsign` and
`GeoChat.to`, sent between two Meshtastic nodes and decoded with both fields
intact. The gateway evidence inspected the fields the gateway *handles*; it did
not carry a live GeoChat two nodes apart. This is software, on upstream's own
ATAK plugin port rather than a channel invented beside it (`AGENTS.md` rule 6),
and it runs the way `.github/workflows/lora-probe.yml` runs its message check --
`meshtasticd` nodes exchanging over the simulated segment.

**Done 2026-09-06.** A `TAKPacket` with `Contact.callsign` and `GeoChat.to`
crossed two `meshtasticd` nodes with both fields byte-identical
(`test/bench/geochat-survival.sh`,
`docs/evidence/TBR-NET-02/2026-09-06-geochat-to-survives-the-meshtastic-bearer.md`).
`FML-ADR-070`'s encoding is carriable on the bearer, so the recipient-resolution
path may be built on `GeoChat.to`.

### What actually blocks tagging behind a MULE

Worth stating plainly, because closing `TBR-NET-02` does not unblock it and it
would be reasonable to assume otherwise.

| Needed | State |
| --- | --- |
| A named owner accepting the specification | Governance. Nothing technical outstanding. |
| The gateway can carry an application tag | **Untested.** The probe above. |
| A mission package participant roster and index | Schema change, named in the specification and deliberately not made. `additionalProperties: false` makes it explicit. |
| A gateway to read and write the tag | `services/gateways/` is a placeholder. `TBR-TAK-01` is now `CLOSED`, so it is blocked on `TBR-RF-02` (hardware) and a catalog decision. **`TBR-RF-02` is the real blocker.** |
| `TBR-ID-01` | **Not required.** The specification separates addressing from authentication on purpose. |

So the critical path to tagging now runs through `TBR-RF-02` (hardware):
`TBR-TAK-01` is `CLOSED`, and the gateway to carry the tag waits on the RF
coexistence trade and a catalog decision.

## Definition of done for anything on this roadmap

From `AGENTS.md`. All five, and say which ones you actually ran.

1. `tools/lint.sh` passes. Read its exit code, not its last line of output.
2. New behaviour has a test that **fails without the change**.
3. Any rule you added is enforced by a check, or you have said plainly why not.
4. If you touched ADR or trade frontmatter, `STATUS.md`, the traceability matrix
   and the decision index are regenerated and committed in the same change.
5. You can name the evidence for every claim you wrote down.
6. **Every doc your change made stale is updated in the same change**, this
   file first. If your change decides a trade, creates one, supersedes an ADR,
   or lands a finding, the `**State:**` line, the item text, or the affected
   README moves with it. A stale State line is the failure this file's own
   single-source rule exists to prevent; leaving one for a follow-up PR is not
   done.

And one more that this roadmap adds, because it is where the time went:

**If your change produced a number, you can state the resolution of the
instrument that produced it.** If you cannot, it is not a number yet. Three
configuration verdicts were recorded as measured results, and all three were
smaller than the resolution of the loop that produced them.

## CONOPS coverage map

The roadmap should be all-encompassing: every operational obligation in the
CONOPS should either be covered by a roadmap item or be visibly a gap. This map
is where that is checked. It is a coarse map, section-group to track, not a
clause-level matrix -- the clause-level trace lives in
`docs/verification/traceability.md` and SAD section 35, and duplicating it here
would rot. This answers the different question of **which part of this roadmap
carries which part of the CONOPS**.

| CONOPS sections | Subject | Carried by |
| --- | --- | --- |
| 1, 4, 5 | Local-first, WAN-independence, design principles | Track 1, and the principle behind every track |
| 6 | EUDs per node, addressing | `1.3`, `1.4` (`TBR-NET-02`) |
| 9 | Service criticality, shedding order | Track 4, and `CCR-02` for the order below S3 |
| 9.2 | S1 local map service (cached maps) | `4.4` |
| 26, 27 | TAK state classes and continuity | Track 3 (`TBR-TAK-01`), Track 4.1 |
| 39-44 | Adaptive routing, traffic preference, WAN gateway/overlay, remote teams | Track 1, `1.5`/`1.5a` addressing, `4.2` for voice paths |
| 45 | External VHF/UHF/HF integration | Track 4.2, 4.3 (`CCR-03`) |
| 46 | Amateur-radio governance | `CCR-03` (voice egress gating); `regions/`, `REGULATORY.md` |
| 50, 51 | Operating modes, exercise control | `1.6` (`RadioState`), `CCR-01` for mode axes |
| 52 | Diagnostic tier | `FML-ADR-046` status aggregator (blocked service) |
| 78, 79, 82, 85 | Qualification stages, success criteria, verification | Track 2, `docs/verification/` and the ITEP |
| 81 | Scope exclusions, non-goals | `docs/NON-GOALS.md`; `CCR-03` moves RoIP off it |
| 86 | Change control | `docs/change-requests/` (`CCR-01`, `CCR-02`, `CCR-03`, `PBCR-01`) |

**Known coverage gaps, stated rather than hidden:**

- **Time** (`TBR-TIME-01`) now has a dedicated item, `4.5`: the readers and the
  per-node decision are built and the partition rule is analysed; the values are
  the open trade. **Storage-at-rest and recovery** (`TBR-SEC-01`, `TBR-REC-01`)
  have decided principles (`FML-ADR-043` LUKS2, `044` crypto-erase zeroize, `050`
  write-amp, `041` rollback) but **no `mule/` code and no dedicated track**. The
  hardware-free half of `TBR-SEC-01` -- whether the unlock method forces a hardware
  root of trust onto the carrier -- is analysed in
  `docs/evidence/TBR-SEC-01/2026-09-20-unlock-method-comparison.md` (it banks the
  software half and feeds `TBR-HW-01`/`TBR-CARRIER-01`; the trade stays `OPEN`).
  The remainder is hardware-gated: `TBR-SEC-01` is `requires-hardware: partly` (the
  unlock/boot demo) and `TBR-REC-01` `requires-hardware: yes` (the rollback demo),
  so they surface where Track 2 hardware work touches them, not as software items.
- **Identity** (`TBR-ID-01`, `FML-ADR-036`/`037`/`038`) is on the critical path
  for the service plane. It now has a dedicated item, `4.6`: the provider
  decision, the RBAC model and identity-aware admission are hardware-free P1 work;
  the credential at rest is `TBR-SEC-01`'s hardware half.
- **Power and thermal** (`TBR-PWR-01`, `TBR-THERM-01`) are Track 2 trades with
  no roadmap item beyond the purchase note, because nothing in software advances
  them.

These gaps are the honest state: the roadmap is network-complete and
service-plane-partial, and this map is what makes that visible instead of
implied.
