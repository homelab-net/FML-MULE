# What each convergence mechanism discloses, and what an operator does

**Trade:** `TBR-NET-03`.
**Date:** 2026-08-31.
**Taken by:** Cameron Zobrist.
**Status of this artifact:** analysis against `THREAT_MODEL.md` and the
measurements already recorded under this trade. No new measurement.

## What this supplies

Two of the trade's four closure-evidence items: the `THREAT_MODEL.md`
assessment, and the statement of what an operator does. The convergence trace is
supplied by `2026-08-30-liaison-routing-exercise.md`, and the interaction with
`TBR-NET-01` is stated in the trade itself.

## The disclosure assessment

### Merging two meshes is an admission decision, taken by radio configuration

This is the finding that matters most and it is not about radio at all.

`THREAT_MODEL.md`, under what the design does **not** defend against:

> The operational domain is a **shared trust environment**. [...] **There is no
> meaningful compartmentation between admitted participants.** Admission is
> close to all-or-nothing at the mission level. **An insider is inside.**

Two deployments that agree a `mesh_id` and form one mesh have therefore admitted
each other's members to one trust environment. Every participant of deployment A
becomes, for the duration, an admitted participant alongside deployment B's, and
the model says plainly that no technical control here compartments them.

**That admission is performed by typing a mesh name into a radio.** It bypasses
whatever admission control either organization operates, because the trust
environment is the layer 2 domain and nothing above it is consulted.

`THREAT_MODEL.md` names the insider as an assumed adversary and says vetting whom
you admit is the primary control and an organisational one. A convergence
mechanism that merges meshes hands that control to whoever configures a radio.

### What each option discloses

| Option | To a passive listener | To the other deployment |
| --- | --- | --- |
| Fixed program-wide `mesh_id` | A constant, published in this repository, that identifies a beacon as a MULE deployment. Permanent and unchangeable. | Everything, always, with no decision taken. |
| Per-deployment `mesh_id` plus a convergence procedure | The agreed name, audible in beacons while converged, and the act of converging is itself visible as a change. | Everything, while converged. |
| Routed liaison | An incident mesh name, audible in beacons, carried by one node per deployment. | Only what is routed. Peer and multicast traffic does not cross a layer 3 boundary. |
| Defer | Nothing beyond what a single deployment already emits. | Nothing. |

**The routed liaison is the only option that separates "we can pass traffic"
from "we are in one trust environment."** The measurement in
`2026-08-30-liaison-routing-exercise.md` shows why: A2 never learns a MAC
belonging to deployment B and never resolves one, so ATAK's peer multicast, ARP
and every other layer 2 discovery mechanism stop at the liaison. What crosses is
what somebody routed.

### What none of them fix

`THREAT_MODEL.md` records that the device has a detectable radio signature and
that "the emissions pattern is close to a fingerprint for this class of device,
and it will become more so as the design is published and copied." A second
bearer on a liaison node adds an emitter. Nothing in this trade improves that,
and the fixed-`mesh_id` option makes it worse by adding a constant to fingerprint
against.

**A capable signals-intelligence adversary is explicitly out of scope** in the
model, and no option here is chosen or rejected on that basis.

## What an operator does

The trade asks for this "in the words an operator would use, for whichever
option is selected", and says that if the procedure cannot be followed by a
volunteer under stress without a laptop, **that is a finding about the option**.

### The liaison procedure, written honestly

1. Agree with the other team which node on each side is the liaison, and one
   name for the incident mesh.
2. On your liaison node, bring up the spare bearer on that mesh name.
3. Check that the two liaison nodes can reach each other.
4. Tell your liaison how to reach their address range, and tell your own nodes
   to reach it through your liaison.

**Steps 1 to 3 are fine. Step 4 is not**, and it is the whole finding.

Step 4 requires knowing and typing another organization's address range, on a
node, correctly, during an incident. `2026-08-30-liaison-routing-exercise.md`
measured the same step as six commands across four nodes. Worse,
`2026-08-31-external-network-collision-analysis.md` shows what a wrong prefix
does: it silently takes part of your own mesh away, and the failure presents as
a radio problem.

**So the procedure as a set of typed commands fails the trade's own test.** It
is not a procedure a volunteer should run under stress, and writing it into a
field guide would be writing down a trap.

### What makes it pass

The same trade already produced the answer, for a different reason. The liaison
exercise found that a hand-typed route does not survive the bearer bouncing,
because the kernel deletes it with the interface, and concluded that **the
routes must be declared, not typed**, under `FML-ADR-059`.

Declaring them solves both problems at once. If the incident mesh name and the
peer range are configuration a node is given, the operator action collapses to:

> Agree the incident mesh name with the other team. Set it on the liaison node.
> Confirm the two liaisons see each other.

That is three steps, no addresses, and nothing to type wrong. **The mechanism is
only acceptable in its declared form**, and that is a constraint on the design
rather than a preference about it.

## What this does not establish

**No operator has tried either version.** This is an assessment of a written
procedure against a stated standard, not an observation of anybody performing
it. CONOPS field-demo stages are where that would be answered.

**Nothing about the trust boundary in operation.** The assessment above says a
routed liaison discloses only what is routed. It does not say what *should* be
routed, who decides, or what a compromised liaison reaches. That is named in the
trade as its own closure item and is still not supplied.

**No credential or admission mechanism is proposed.** The finding that merging
meshes bypasses admission control is a reason to prefer a mechanism that does
not merge them. It is not a design for admitting another organization's members
deliberately, which nothing in this program currently has.
