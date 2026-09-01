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
recipient rides as a deployment-scoped one-byte tag inside the payload.

The trade is still `OPEN` and cannot close, because every owner is `TBD-SRR`.
That is a governance gap rather than a technical one: the specification is
enough to shape an interface against, and an interface built to it will not have
to be replaced by the act of a named owner signing the same document.

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

**The trade has a named owner and is still `OPEN`.** Cameron Zobrist owns it,
so the governance blocker is gone. Nothing technical is missing for the IP
half.

**What is missing now is a decision, and it is not the one the specification
expected.** `2026-08-30-opentakserver-meshtastic-path.md` read the first of
`FML-ADR-048`'s three gateways and found two things. A payload on a private
port is discarded by it, which is where a custom one-byte member tag would
sit. And the ATAK plugin protobuf it does handle already carries
`Contact.callsign` and `GeoChat.to`, so identity and recipient are on the wire
already, as upstream's strings rather than this program's index.

So the specification's chosen encoding is not available in combination with
`FML-ADR-048`: adding the index means replacing upstream's format, which that
ADR orders the program not to do first. The owner picks between using what
upstream carries, at more airtime, or keeping the index and writing an ADR
against `FML-ADR-048`. Neither is implementation work and both are decisions.

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
`docs/evidence/TBR-NET-02/` and a named owner accepts them. See the Track 3
blocker: no trade can close while every owner is `TBD-SRR`.

**Traps:** the natural implementation of "cannot resolve the recipient" is to
deliver to everyone. It looks like helpfulness and CONOPS section 23 makes it
wrong, which is why the trade states the fail-closed rule as a gate rather than
leaving it to the analysis.

### 1.5 `TBR-NET-01`, the addressing plan

**State:** the decision is made -- **`FML-ADR-063`, `SELECTED`** -- and the
trade is **ready to close on the named owner's acceptance**. All three
closure-evidence items exist under `docs/evidence/TBR-NET-01/` and a decision is
in the register; SAD section 30.2 makes acceptance the remaining step, which is
the owner's act, not the author's.

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

**Done when:** evidence under `docs/evidence/TBR-NET-01/` accepted by a named
owner. See the blocker in Track 3; today no trade can close.

### 1.5a `TBR-NET-03`, how two deployments converge

**State:** open, raised 2026-08-30. **A decision exists -- `FML-ADR-061`,
`SELECTED`** -- and four artifacts support it. `FML-ADR-060` was superseded the
day after it was written and must not be read as current.

The mesh is keyed with `key_mgmt=SAE`, MULEs of one deployment merge
automatically on a shared credential, and a partner gets a **separate keyed
mesh** on a liaison node so the boundary is revocable without rekeying the
fleet. Measured: a node without the credential never reaches `ESTAB`;
`test/bench/keyed-mesh.sh` reproduces it.

**It still does not close.** One closure item is unsupplied -- what a liaison
may forward and who authorises one -- and the liaison half stays conditional on
1.5 selecting per-deployment prefixes.

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

**State:** a `Protocol` in `test/flatsat/interfaces.py` with two methods,
`enumerated()` and `associated()`, and a fake behind it.

**Blocked by:** not by a trade, but sequence it after 1.2. Reading real radio
state is worth little until something brings radios up in a known order.

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

## Track 2 — hardware

**State:** unchanged. No hardware selected, no image built, nothing in this
repository has met a radio.

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

**It closes nothing by itself.** SAD section 30.2 says a TBR closes when its
listed evidence exists, the named owner accepts it, **and the resulting
architecture decision is entered into the ADR register**. The third condition is
unmet everywhere: no trade in this repository has a decision written against it
yet. `TBR-NET-01` is the closest -- all three of its closure-evidence items now
exist -- and it still cannot close, because it has no decision and because it
depends on `TBR-NET-03`.

**The other half of the SRR exit action is still open.** Section 30.2 asks for a
named individual *and a calendar target date*. Every `target-date` is still
`TBD-SRR`, deliberately: a date is a commitment and inventing one would be
inventing a specification. That remains the Program Owner's to set.

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

### The one remaining SRR item is blocked, and not on us

Target dates. Every `target-date` is `TBD-SRR`, and setting them is not a typing
task:

**Every closure gate is a milestone, and no milestone has a date.** From the
section 30.2 register: hardware PDR, host selection, hardware/enclosure PDR,
RF/BOM lock, HW/HA/security lock, hardware block lock, production software PDR,
HA architecture lock, PDR, RF design lock, CDR-lite, production image baseline,
Security Architecture lock, ICD baseline, production hardware-block lock.

Section 30.2 is explicit about why they are undated: *No calendar schedule has
yet been baselined for FML/MULE. This SAD therefore does not invent dates.*

So the SRR exit action needs **a baselined program schedule**, and the trade
dates fall out of it. That reduces the task from eighteen dates to roughly
fifteen milestones, and it is the Program Owner's, not this repository's.
Inventing dates here would be inventing a specification.

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

**State, 2026-08-31: well advanced, not closed.** Seven evidence artifacts
exist, including a **running OpenTAKServer instance** with PyTAK clients. The
closure gate's classification half is met: all 41 tables classified into CONOPS
section 26 classes, plus the state outside the database. Of the six empirical
items the analysis listed, **three are closed** -- durable-queue inspection (no
durable queue exists), the different-node restore (restores every row,
authenticates nobody, because the salt and CA live in `OTS_DATA_FOLDER`), and the
relational decomposition -- **one answered from source** (durable state
locations), and two of the four workflow tests are done (mission API, certificate
enrollment). What remains: DataSync content, mission-package upload, the map-cache
question, and the named owner's acceptance.

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

**State:** the state study is well advanced (`TBR-TAK-01`, seven evidence
artifacts) and the implementation is not started, but the shape is now known
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
`FML-ADR-035` for service control, and the seven `TBR-TAK-01` artifacts, which
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
`FML-ADR-067`, all `PROPOSED`.

**State:** proposed, not approved. The whole capability is a CONOPS v1.1 change,
`CCR-03`, and nothing here is built or should be until that is approved. The
decisions are allocated so the identifiers are fixed: DM-32UV as the radio
(`FML-ADR-064`), audio/PTT over IP not native DMR (`FML-ADR-065`), a dedicated
integrated gateway radio (`FML-ADR-066`), and the single-audio-egress invariant
(`FML-ADR-067`).

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
  distribution that `TBR-SEC-01` records as absent.

### 4.4 A local map service

**CONOPS basis:** section 9.2 (S1 local mission services -- "selected cached
maps"), and the high-rate bearer's "map packages" purpose. Decision: none yet;
the selection is `TBR-MAP-01` and the service outline is `services/map/README.md`.

**State:** a gap, surfaced 2026-08-31 by the question "why can't we have map
cache". Two things were being conflated. **Device-side tile caching** is an ATAK
client function -- the client caches tiles it renders -- and is what
`TBR-TAK-01`'s cache question (item 6) is about, which is why that item needs a
real client. **Serving maps locally** is a different thing: not a TAK-server
function at all (OpenTAKServer handles no tiles), not ATAK-only, and per CONOPS
section 9.2 a **MULE S1 service**. The TAK server is S2. So maps sit in a
*higher* availability tier than TAK and are supposed to remain when TAK is gone.

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
minutes; `TBR-TAK-01` itself was worked this session and is well advanced. Track
4 is blocked at the catalog gate for the services and on `CCR-03` for voice, but
its analysis, the TAK state study, is largely done.

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

### The gateway tag probe

`docs/evidence/TBR-NET-02/2026-08-29-addressing-specification.md` lists three
things that would falsify it. The third is the one nobody has tested:

> **If the gateway cannot carry an application tag** in the payload alongside
> the message, the encoding above is unimplementable and option D, one radio
> per EUD, becomes the serious alternative. `FML-ADR-048` fixes the gateway
> order and none of the three has been exercised.

That is answerable in software, the same way 1.1 step 1 answered whether the
LoRa plane could be exercised at all, and for the same reason: a design built
on an untested assumption is worth less than the assumption is worth checking.
It costs one probe and it can invalidate a specification that is otherwise
ready to close.

**Do it before anything is built on the tag**, not after.

### What actually blocks tagging behind a MULE

Worth stating plainly, because closing `TBR-NET-02` does not unblock it and it
would be reasonable to assume otherwise.

| Needed | State |
| --- | --- |
| A named owner accepting the specification | Governance. Nothing technical outstanding. |
| The gateway can carry an application tag | **Untested.** The probe above. |
| A mission package participant roster and index | Schema change, named in the specification and deliberately not made. `additionalProperties: false` makes it explicit. |
| A gateway to read and write the tag | `services/gateways/` is a placeholder blocked on `TBR-TAK-01` (`CRITICAL`) and `TBR-RF-02`. **This is the real blocker.** |
| `TBR-ID-01` | **Not required.** The specification separates addressing from authentication on purpose. |

So the critical path to tagging runs through `TBR-TAK-01`, which needs no
hardware and is Track 3 item one.

## Definition of done for anything on this roadmap

From `AGENTS.md`. All five, and say which ones you actually ran.

1. `tools/lint.sh` passes. Read its exit code, not its last line of output.
2. New behaviour has a test that **fails without the change**.
3. Any rule you added is enforced by a check, or you have said plainly why not.
4. If you touched ADR or trade frontmatter, `STATUS.md`, the traceability matrix
   and the decision index are regenerated and committed in the same change.
5. You can name the evidence for every claim you wrote down.

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

- **Time, storage-at-rest, and recovery** (`TBR-TIME-01`, `TBR-SEC-01`,
  `TBR-REC-01`) have decisions and `mule/` readers but no dedicated roadmap
  track; they surface only where another item touches them. They belong to Track
  2 and Track 4 work not yet written up as items.
- **Identity** (`TBR-ID-01`, `FML-ADR-036`/`037`/`038`) is on the critical path
  for the service plane and appears only inside `4.1`'s findings and the
  `X-Ssl-Cert` work in `services/ingress/`. It needs its own item under Track 4.
- **Power and thermal** (`TBR-PWR-01`, `TBR-THERM-01`) are Track 2 trades with
  no roadmap item beyond the purchase note, because nothing in software advances
  them.

These gaps are the honest state: the roadmap is network-complete and
service-plane-partial, and this map is what makes that visible instead of
implied.
