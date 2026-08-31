# The option this trade does not list, and the standard written for its question

**Trade:** `TBR-NET-01`.
**Date:** 2026-08-31.
**Taken by:** Cameron Zobrist.
**Status of this artifact:** analysis. **No measurement.** It reported that the
trade's option space was incomplete. **The option it names has since been
excluded by the Program Owner; see Disposition at the end.** The analysis is
retained because the reasoning behind an exclusion is worth as much as the
reasoning behind a selection.

## Why this exists

`TBR-NET-01` asks: *"Retain `10.41.0.0/16` or select another field prefix?"*
Both options are IPv4. Four artifacts under this trade have now established what
that costs:

- Two deployments sharing a prefix conflict silently, and `FML-ADR-061` makes
  automatic merging the normal case rather than the exceptional one.
- Any external route more specific than the mesh prefix takes that slice of the
  mesh away, with nothing logged.
- **No routing mechanism fixes that.** Policy routing moves the loss; only a VRF
  separates the two networks, per application, and no application sees both.

The remaining question was framed as "can the mesh hold address space an uplink
will not also claim". **There is a standard whose entire purpose is answering
that, and this trade does not list it.**

## RFC 4193, Unique Local Addresses

A ULA prefix is `fd00::/8` followed by a **randomly generated 40-bit global
ID**, giving a `/48` per site. The randomness is not incidental; it is the
mechanism. RFC 4193 exists so that independently administered networks which
were never coordinated can be interconnected later without renumbering.

That is `TBR-NET-01`'s question, stated by a standards body, with a published
answer.

Against what the artifacts under this trade measured:

- **Deployment against deployment.** Two independently generated ULA prefixes
  collide with probability about 2^-40. Two deployments both retaining
  `10.41.0.0/16` collide with certainty, which
  `2026-08-30-collision-exercise.md` recorded.
- **Deployment against a venue.** A venue LAN hands out IPv4 and installs IPv4
  routes. **It cannot claim an `fd00::/8` destination**, so the
  longest-prefix-match failure in
  `2026-08-31-external-network-collision-analysis.md` and every trade-off in
  `2026-08-31-no-routing-mechanism-fixes-an-ambiguous-address.md` does not
  arise. The ambiguity that no routing mechanism could resolve is not created in
  the first place.
- **No coordination.** Unlike a per-deployment IPv4 prefix, nothing has to be
  agreed, allocated or registered between organizations.

## The procedural path exists and does not block

SAD section 4.4 is short, and its **only** stated reason is a parent-baseline
one:

> The parent Homelab currently disables managed IPv6.
>
> MULE v1 therefore remains IPv4-first and does not introduce a separate managed
> IPv6 architecture during initial qualification.
>
> IPv6 may be reintroduced only through controlled parent and subsystem change.

**IPv6 is not excluded on its merits for the field mesh.** It is excluded
because the parent disables it, and the exclusion is explicitly reversible
through controlled change.

`docs/change-requests/` carries that mechanism, and `PBCR-01` is a precedent:
parent-baseline change requests are "changes the MULE subsystem requires in the
parent Homelab baseline" and the README states **"These do not block MULE
work."**

## The deciding question, and it is not addressed here

**Whether the applications work over IPv6.** ATAK, the TAK server,
`meshtasticd`, `dnsmasq` and the browser services. If they do not, none of the
above matters, and this is untested.

It is the same unknown recorded for link-local in
`docs/evidence/TBR-NET-03/2026-08-30-what-happens-with-no-configuration.md`, but
weaker there: link-local needs a scope on every address, which software
mishandles. **A ULA is an ordinary routable global-scope address** and carries
none of that difficulty, so software that fails on link-local may still work on
a ULA. Neither has been tried against a real service.

`TBR-TAK-01` and the `services/` catalog are where that would be established,
and `TBR-RF-02` blocks the gateway work.

## Costs and objections, stated rather than argued away

**Dual-stack keeps the IPv4 problem.** If anything remains IPv4 on the mesh, its
collisions remain exactly as measured. A ULA helps only what runs on it.

**`THREAT_MODEL.md` still applies to the host part.** The prefix is random and
carries no node identity, which is better than an IPv4 address derived from a
durable node identifier. But an interface identifier formed from a MAC address
is a durable identifier, which is the concern that file already records. Stable
privacy addressing exists and is not evaluated here.

**batman-adv is layer 2** and carries IPv6 without modification, so the bearer
is not an obstacle. That is the easy part and should not be mistaken for the
hard one.

**It is a change request against a controlled document**, with the delay and
approval that implies. This artifact does not claim that is cheap.

## What this artifact does and does not do

It **does** report that the trade's stated options are incomplete, and that a
decision made against them would be made against an option space that omits the
standard written for the question.

It **does not** select ULA, propose a change request, or assert that the
applications work. Selecting an option is the trade's job and the named owner's
acceptance, and this program has already superseded one ADR for deciding ahead
of its evidence.

## Disposition: excluded, 2026-08-31

**The Program Owner has excluded IPv6 for MULE v1**, on a ground this artifact
did not weigh: **broader hardware support, and older systems in the mesh.**

CONOPS plans four to eight **volunteer-owned** EUDs per MULE. The program does
not choose what a volunteer brings, and `FML-ADR-038` already accepts "the
provisioning burden of per-device certificates on volunteer-owned EUDs" and
names "EUD client compatibility" as an operational burden on the Communications
and Identity Management function.

Requiring IPv6 of those same devices is a larger burden with a harder failure
mode. An EUD that is awkward to provision still works once provisioned. **An EUD
whose stack does not do IPv6 well does not work at all**, and a volunteer
disaster response cannot turn away a responder because their tablet is old.

**That outweighs the addressing property**, and this artifact accepts the
decision rather than arguing it. An addressing scheme that is elegant and
excludes participants is the wrong trade for this program.

### What the exclusion costs, so nobody thinks the problem went away

Every measurement under this trade stands, and the IPv4 failures are now the
ones the program will live with:

- Two deployments sharing a prefix conflict **silently**, and `FML-ADR-061`
  makes automatic merging the normal case.
- A venue LAN overlapping the mesh prefix takes that slice of the mesh away,
  with nothing logged.
- **No routing mechanism fixes the second one.** Policy routing moves the loss;
  a VRF separates the two networks only per application, and requires every
  mesh-using application to bind into it.

The trade must therefore be decided inside IPv4, knowing that **the venue-overlap
failure has no clean answer** and the decision has to say what a node does about
it rather than what prevents it.

**IPv4 link-local, RFC 3927, is not a substitute** and is not proposed. It is not
routable, Debian does not configure it by default, and it carries none of the
per-site randomness that made a ULA relevant here.
