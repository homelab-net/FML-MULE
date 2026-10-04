# How a node assigns the EUD access-point subnet and DHCP

**Trade:** `TBR-NET-05`.
**Date:** 2026-10-03.
**Taken by:** Repository agent. **Independently verified** before filing; the
verifier rejected an earlier draft as closure and the corrections are carried
below.
**Status of this artifact:** written analysis. **No hardware is required and
none was used.** Nothing here is a measurement.

**This is a finding that narrows the trade. It is not closure.** Gate element 2
asks for "the DHCP range and lease" and this supplies a sourced basis for the
range and **no lease**, so `TBR-NET-05` stays `OPEN` on that half. The precedent
is `TBR-OBS-01`, recorded in `docs/trades/README.md`: "The comparison is
written. It does not select a representation. Accepting that finding does not
close the trade."

## What an earlier draft of this file got wrong

Recorded because the correction is more useful than the conclusion.

This document first asserted that **"no document decides DHCP authority for the
mesh"**. That is false. `docs/architecture/FML-MULE-SAD-v0.32.md` line 456:

> Per-node DHCP allocation follows the upstream OpenMANET principle of
> non-overlapping local scopes.

That is precisely the answer the draft "selected" after rejecting the
alternative. The draft quoted SAD section 4.3 at lines 450-454 and **stopped one
blank line short** of the sentence answering its own question, having searched
for phrasings like "DHCP authority" rather than running `grep -i dhcp` over
`docs/architecture/`. `AGENTS.md` names this failure by example -- a 31.5 s delay
written up as unexplained when the repository already carried the cause, in this
same directory. Same shape, same cost.

So the reasoning below is **derivation from SAD 4.3**, not discovery. What
genuinely remains undecided is the *mechanism*: SAD decides non-overlapping
per-node scopes and says nothing about how a scope is assigned.

## The question is wrongly shaped, and that part stands

The trade asks what subnet "a node hands to the phones on its EUD access point".
On a meshed node **the access point is not a separate broadcast domain.**

SAD section 4.3: "Local EUD access is bridged into the field BATMAN domain."
`FML-ADR-056` constrains that bridge to contain only EUD access-point interfaces
alongside the mesh interface. So two MULEs with five EUDs each are one flat
broadcast domain and the EUDs are on it.

The trade's options list rejects "derive the AP subnet from the field prefix"
because an AP-only node fields no mesh. True for that shape, **false for a
meshed node**, where deriving from the deployment prefix is the only coherent
answer: a second layer-3 network on one layer-2 segment is a misconfiguration,
not a collision risk.

## 1. Subnet form

**Per-deployment, carried in the mission package. Not fixed, not per-node.**

| Shape | Verdict |
| --- | --- |
| Fixed program-wide constant | **Rejected.** `FML-ADR-063` declined to retain `10.41.0.0/16` as a program-wide constant on collision and OPSEC grounds that transfer unchanged. `test/bench/mule-ap-up.sh` currently hardcodes `10.41.0.0/24`, inside that very range. |
| Per-node subnet | **Rejected.** Puts two layer-3 networks on one bridged layer-2 segment. |
| Derived from the field prefix | **Correct for a meshed node.** Impossible for an AP-only one, which has no prefix. |
| Per-deployment, in the mission package | **Selected**, mirroring `network.address_prefix`. |

**Reconciliation rule, which the earlier draft omitted.** A node may hold both an
`address_prefix` and an AP subnet field -- an AP-only node that later joins a
mesh is the ordinary case, not a corner one. **When a node fields a mesh bearer,
`address_prefix` governs and the AP subnet field is not used.** Without that rule
the renderer has two candidate answers and no tiebreak.

**There is a second subnet, and it is not this one.** `FML-ADR-084` decides that
onboarding uses a separate isolated BSS, and its consequences require "a
quarantine bridge or VLAN, **DHCP/DNS scoped to it**, and fail-closed firewall
rules". The earlier draft asserted flatly that there is no second subnet, which
contradicts a `SELECTED` ADR. The onboarding scope is a distinct address space
from the operational one and **this trade does not decide it**; whether it falls
to `TBR-NET-05` or needs its own owner is an open question this artifact raises
rather than answers.

## 2. DHCP range and lease — the half that stays open

**Principle, from SAD 4.3:** per-node allocation, non-overlapping local scopes.
Every MULE runs an access point and therefore a DHCP server, and `FML-ADR-056`
puts them on one broadcast domain, so the scopes must not overlap. One authority
per deployment would be cleaner and fails the mission: a node that loses the mesh
must still serve the EUDs in front of it.

**Range, proposed with a sourced basis.** `TBR-NET-01` records that "CONOPS plans
four to eight volunteer-owned EUDs per MULE". A **`/24` slice per node inside the
`/16` deployment prefix** gives 254 usable addresses against a planned 4-8, and
256 such slices per deployment. The headroom is deliberate: SAD C6-01 assigns the
*maximum* EUD count to Stage 2 testing under `TBR-RF-01`/`TBR-RF-03`, so the
planning figure is not a ceiling and address space inside a `/16` is free.
**Proposed, not decided** -- the extent belongs in the ADR with the Owner's
acceptance.

**Node addresses must be reserved out of the slices.** A node's own mesh address
comes from the same `address_prefix` (`FML-ADR-063`). Nothing currently stops an
implementer placing a node address inside a peer's DHCP pool. The ADR must say
where node addresses live relative to the slices.

**Slice assignment mechanism: undecided.** Whether a slice comes from a per-node
index in the mission package or is generated alongside the prefix is the real
residual, and SAD 4.3 does not reach it.

**Lease: no value, and `TBR-NET-05` stays `OPEN` on it.**
`os/config/dnsmasq.conf.template` records that nobody has measured it -- "short
enough that a device moving between nodes recovers quickly, long enough not to
churn" -- and both bounds are real and opposed. `AGENTS.md` requires a duration
to be sourced to a measurement or written `TBD` **citing the trade that will
decide it**; the owner here is this trade, which therefore does not close on this
element. `test/bench/mule-ap-up.sh`'s `12h` is a bench literal and is not
laundered into a field value. The measurement needs hardware and a client moving
between nodes, which is M2 and beyond.

## The sharpest practical consequence, which the earlier draft missed

**`os/config/dnsmasq.conf.template`'s own scoping mitigation cannot work under
the bridging this trade depends on.** The template carries:

```text
interface=TBD                  # EUD access point interface only.
bind-interfaces
# Do NOT serve DHCP or DNS onto the mesh.
```

If the AP interfaces are bridge ports alongside `bat0`, then dnsmasq binds the
**bridge**, and the mesh is inside it. `interface=<ap>` plus `bind-interfaces`
has no interface boundary left to scope on, so the instruction not to serve onto
the mesh cannot be honoured by that mechanism. This is the most load-bearing
output of the reframing and it needs an answer before any `dnsmasq` render.

## 3. Where the value lives

**The mission package**, as new fields under `network`, alongside
`address_prefix`.

Not the region profile: this is a deployment property and `regions/` carries what
a regulator decides. Not a constant: rejected above.
`mission/schema/mission-package.schema.json` sets
`network.additionalProperties: false` and `mule/mission.py` validates against it
with a `Draft202012Validator`, so an unknown field is a hard error rather than a
silent skip -- the behaviour wanted.

## 4. The collision argument

**Between deployments.** `FML-ADR-063`: "Two deployments sharing a prefix
conflict silently. One wins ARP, the other degrades." A fixed AP subnet makes
that certain rather than possible.

That ADR also argues a generated value carries no identity, because an address
derived from a durable node identifier is itself a durable identifier.
**Attribution correction:** `FML-ADR-063` lines 48-51 and the schema's
`address_prefix` description both attribute that to `THREAT_MODEL.md`, which
contains no such statement -- checked 2026-10-03. The reasoning stands on the
ADR; the citation does not, and the defect is inherited rather than introduced
here. It is recorded so it can be fixed at its source.

**Within one deployment, which is the stronger argument.** Two MULEs at one
incident are not two networks that might meet; they are one broadcast domain by
design, immediately, every time. The inter-deployment argument makes a constant
unwise. The intra-deployment one makes a per-node subnet **wrong**.

## 5. Fail-closed behaviour when the value is absent

**A node that fields an access point and has no subnet value shall refuse to
raise it**, and report why.

**Nothing implements this today, and that is stated rather than implied.** The
earlier draft claimed it "follows the posture already built". It does not:

- `mule/configuration.py`'s refusal is `_is_tbd()`, a string comparison against
  `"TBD"` on **region profile** parameters. An absent mission-package field is
  not a `TBD` string.
- The fail-closed boot path (exit 5 at `mule/configuration.py:824`, implementing
  `FML-ADR-083`) renders **hostapd only**; `mule/rendering.py:153` explicitly
  emits that DHCP/DNS and addressing are gated and rendered elsewhere.
- `network.required` is `['mesh_id']` only, so an absent AP subnet field is not
  a schema error.

So this `shall` is a requirement with **no check**, which `AGENTS.md` permits
only if said plainly. Said plainly: the check does not exist. Making it exist
means either adding the field to `network.required` or extending the refusal
path, and that belongs with the ADR that decides the field.

`FML-ADR-074` ("a node that cannot serve users **shall** be reported `FAULT`")
is the state the refusal should surface, and it is already decided.

## What this does not settle

- **The lease.** No value. `TBR-NET-05` stays `OPEN` on gate element 2.
- **The slice extent.** Proposed with a sourced basis; the Owner decides.
- **The slice-assignment mechanism.** Undecided, and SAD 4.3 does not reach it.
- **The onboarding scope** (`FML-ADR-084`). Needs an owner.
- **The dnsmasq scoping problem.** Named, not solved.
- **The local domain.** No trade owns it; recorded in
  `services/ingress/README.md`.
- **Anything measured.** No node ran, no lease was issued, no collision was
  observed.
- **`v0.0.1` is not blocked on the multi-node half.** The M1 article is one
  AP-only node; the scope-overlap question bites at two.
