# Remote name resolution across multiple MULEs: split-DNS cannot fan out

**Trade:** `TBR-NET-06`.
**Date:** 2026-09-29.
**Taken by:** Cameron Zobrist, on the lab development machine.
**Status of this artifact:** analysis **by reasoning, no bench**. It records the option
comparison `TBR-NET-06`'s closure gate asks the owner to make, and recommends a direction. It
does **not** close the trade: the closure gate requires an observation on a real two-MULE tailnet
(the two-Pi bring-up), which this artifact does not have and a `netns` model cannot substitute for
(see "What this does not establish").

## The open question

`FML-ADR-031` fixes one stable service name (`tak.field`) an EUD never changes. `FML-ADR-082`
makes the assigned MULE the boundary, with no silent failover to another MULE. `FML-ADR-086` gives
each MULE a per-MULE overlay identity and leaves the remote ingress a named `TBD`. None of them
decides **how the name resolves to the assigned MULE over the overlay** when several MULEs share
the tailnet. `TBR-NET-06` asks exactly that.

The single-MULE case is demonstrated: on the bench a real iOS TAK client reaches the one name on
both the local access point and the Tailscale overlay, because a per-domain split-DNS entry routes
the name to the one MULE's resolver. That is the mechanism this analysis shows cannot generalize.

## Why tailnet-global split-DNS cannot fan out (the load-bearing point)

Tailscale split-DNS is a **tailnet-wide** setting: a domain (here `field`) maps to a nameserver
(or a set), and **every** node on the tailnet routes queries for that domain to the same
nameserver. There is no per-source (per-EUD) or per-assignment variant of the split-DNS map. So
with two MULEs, a single `field` -> nameserver entry sends **all** EUDs' `tak.field` queries to one
resolver, which returns one answer. An EUD assigned to MULE-2 receives MULE-1's address -- the
wrong MULE -- and, worse, silently, which also cuts against `FML-ADR-082`'s "no failover to another
MULE." The property is structural to split-DNS, not a tuning problem: one global map cannot encode
a per-EUD answer. Any solution must therefore vary the resolver **per EUD/device** or vary the
**name**, not the tailnet-global map.

## Locked constraints any mechanism must honor

- **One stable name** (`FML-ADR-031`): the EUD references `tak.field`; its settings never change
  when a service moves.
- **Assigned-MULE-only, no silent failover** (`FML-ADR-082`): resolution must reach the assigned
  MULE and must not quietly resolve to a different one.
- **Per-MULE identity; ingress owned elsewhere** (`FML-ADR-086`): the target is the assigned MULE's
  per-MULE identity, and the ingress service/port stays `TBD` (PBCR-01 / roadmap 4.6) -- a
  resolution mechanism must not invent it.
- **Local-first, no central directory** (CONOPS §25 + local-first `[SHALL]`, `NON-GOALS.md`): no
  fleet-wide replication, no dependence on a central resolver.

## The options

| Option | One name (031) | Assigned-only, no failover (082) | Per-MULE identity, ingress TBD (086) | Local-first, no central dir | Depends on / status |
| --- | --- | --- | --- | --- | --- |
| 1. Per-EUD/per-device resolver at enrollment (EUD's `.field` resolver = its assigned MULE) | Keeps one name | Yes -- resolver is the assigned MULE; no global map to mis-route | Resolves to the assigned MULE's identity; ingress stays TBD | Yes -- resolver is the local assigned MULE, no central directory | Needs a per-device config channel at enrollment (roadmap 4.6 managed profile/QR); 4.6 partly open |
| 2. Per-MULE names (`tak-<mule>.field`) | **Breaks** one name | Yes | Compatible | Yes | Would need a CONOPS/`FML-ADR-031` change -- out of this trade |
| 3. Tailnet-global split-DNS (status quo) | Keeps one name | **No** -- one global answer mis-routes and fails silently | N/A | Yes | Demonstrated failure; single-MULE only |
| 4. Central mapping / coordination resolver | Keeps one name | Could, if correct | Could | **No** -- central directory | Rejected by local-first |
| 5. MagicDNS per-node names | **Not** the stable one name | Yes | Compatible | Yes | Breaks `FML-ADR-031` |
| 6. Do nothing | Keeps one name | Single-MULE only | N/A | Yes | Accept single-MULE remote reach only |

**Direction, not a decision:** option 1 (per-EUD/per-device resolver set at enrollment) is the only
candidate that keeps the one stable name, reaches the assigned MULE without a global map that can
mis-route, and stays local-first. It is recommended **as a contingent direction**, not a
selection: it presupposes the roadmap 4.6 enrollment/onboarding channel to push the per-device
resolver config, and it binds to the `FML-ADR-086` per-MULE identity -- both of which are owned
elsewhere and partly unbuilt. Its final selection **awaits the real two-MULE tailnet observation**
in the closure gate. The owner records the comparison; the ADR for the chosen mechanism follows
that observation, not this note.

## What this establishes

- The tailnet-global split-DNS constraint is structural, so the single-MULE mechanism cannot
  generalize -- multi-MULE remote reach needs a per-EUD resolver or a per-MULE name.
- Against the four locked constraints, option 1 is the only fit that does not require changing a
  locked decision or a central directory; the rest are ruled out by a named constraint.

## What this does not establish

- **Nothing on real Tailscale or hardware.** This is reasoning, not a measurement. A `netns` bench
  was deliberately **not** built: `netns` has no Tailscale split-DNS mechanism, so it could only
  show two hand-configured resolvers returning different answers -- a tautology that says nothing
  about the tailnet-global constraint and could not be cited toward real behavior.
- That option 1's enrollment channel exists -- roadmap 4.6 is partly open; this does not build it.
- The remote ingress service/port -- left `TBD` (`FML-ADR-086` / PBCR-01), not invented here.
- The `no-silent-failover` behavior under a real assigned-MULE outage -- an `FML-ADR-082`
  observation owed on the two-MULE tailnet.

## Cross-references

- `docs/adr/FML-ADR-031-local-dns-haproxy-service-ingress.md` (one stable name),
  `docs/adr/FML-ADR-082-optional-remote-eud-overlay-membership-ends-at-the-assigned-mule.md`
  (assigned-only), `docs/adr/FML-ADR-086-the-wan-overlay-acl-is-deny-by-default-grants-scoped-to-the-assigned-mule.md`
  (per-MULE identity; ingress TBD).
- `docs/change-requests/PBCR-01-field-service-plane.md` and `docs/ROADMAP-DEV.md` item 4.6 (ingress
  definition and enrollment channel -- named dependencies).
- `docs/evidence/stage-06-wan-overlay/2026-09-29-assigned-ingress-only-real-tailnet.md` (the
  per-MULE identity working on a real tailnet -- the layer this resolution sits above).

Nothing real: no deployment location, member identity, callsign, credential, tailnet identifier, or
operational capture. See `SECURITY.md`.
