# What a liaison may forward, and who authorises one

**Trade:** `TBR-NET-03`.
**Date:** 2026-09-04.
**Taken by:** Cameron Zobrist, with Claude Code, on the lab development machine.
**Status of this artifact:** written analysis for owner acceptance. No
measurement; the mechanism it bounds is `FML-ADR-061`'s routed liaison.

## Why this exists

`TBR-NET-03`'s closure evidence requires, for a liaison mechanism, "a statement
of what it is permitted to forward and who authorises one. A node routing between
two organizations that have not authenticated each other is a trust boundary, and
an unstated boundary is one nobody is enforcing."
`2026-08-31-what-it-discloses-and-what-an-operator-does.md` deferred it
explicitly: it "does not say what *should* be routed, who decides, or what a
compromised liaison reaches." This supplies that statement. It is policy that
follows from decisions already taken, not a new mechanism.

## What a liaison may forward

**Default deny. A liaison forwards only explicitly enumerated flows, and nothing
else.** This is the same posture `os/config/nftables.conf.template` takes and the
same principle `FML-ADR-057` states for what a node may act on: a rule exists
because something named needs to pass, and the reason is written on the rule.

Concretely, a liaison **shall**:

- forward only the specific mission-service reachability the two deployments have
  agreed on, each flow named by service and direction, the way a firewall rule
  is named -- never "all traffic between the two meshes";
- route at layer 3 only. It **shall not** merge the two meshes at layer 2:
  `FML-ADR-061` selected the routed liaison precisely so the meshes do not merge,
  because merging is an admission decision taken by radio configuration that
  bypasses admission control;
- keep the two deployments on **separate keyed meshes** (`FML-ADR-061`), so the
  boundary is revocable by removing the liaison's routes and credentials without
  rekeying either fleet.

A liaison **shall not** forward:

- EUD access-point traffic across the boundary (the EUD trust boundary is the
  node's own, `THREAT_MODEL.md`; a liaison does not widen it to another org);
- the secure WAN overlay (`FML-ADR-039`). CONOPS section 43 keeps a MULE the
  overlay boundary for its own EUDs, and a liaison to a foreign deployment is
  further out still: the overlay reaches program infrastructure and other MULEs,
  and a partner who has not authenticated to the program has no path to it;
- anything not enumerated. There is no general-purpose transit default, and the
  absence of a rule is a denial, not a gap.

## Who authorises one

**A liaison is a declared, authorised role, not an act of radio configuration.**
The `THREAT_MODEL.md` finding this answers is that merging meshes by configuring
a radio bypasses admission control. The remedy is that establishing a liaison is
an explicit, auditable authorisation:

- the liaison role and its enumerated forward set **shall** be declared in the
  mission package of the node that holds it, so that authorising a liaison is a
  change to a controlled artifact that a named authority issues, not something a
  field operator improvises on a radio;
- the authorising party is the **deployment authority** who owns that mission
  package -- the same authority that admits the deployment's own members. A
  liaison to a partner is that authority deciding to route to an organization it
  has not admitted, and the decision is recorded where every other admission
  decision for that deployment is.

This does not propose an admission mechanism for a **partner's members**: the
program has none, and the routed liaison is chosen so that it does not need one
-- the partner's members are never admitted to this deployment's mesh, only
specific flows are routed to them. Inventing member-level cross-admission is out
of scope and is named here so it is not mistaken for solved.

## What a compromised liaison reaches

Bounded by the two rules above. Because forwarding is default-deny and
enumerated, a compromised liaison reaches only the flows it was authorised to
route; because the meshes are routed and not merged, it does not gain either
mesh; because the boundary is revocable (`FML-ADR-061`), the response to a
suspected compromise is to withdraw the liaison's routes and credentials, which
does not disturb either deployment's own operation.

## Bearing on closure

This supplies the last outstanding closure-evidence item for `TBR-NET-03`. What
remains is a **sequencing gate, not more evidence**: the trade's gate holds that
a liaison mechanism "is not accepted while `TBR-NET-01` remains open," because
converging is what makes the addressing collision reachable. `TBR-NET-01` now has
all three of its closure items and is ready for acceptance; once it closes,
`TBR-NET-03` can be accepted on this and the four prior artifacts. The dependency
runs that way and not in a circle: `FML-ADR-063` is unconditional and was taken
accounting for `TBR-NET-03`.
