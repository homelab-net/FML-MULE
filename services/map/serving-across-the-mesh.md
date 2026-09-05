# Serving maps across the mesh

How an EUD gets a map, what happens when its own MULE has no repository, and why
that is a fallback rather than the primary model. This is the design for the
"map server for the mesh" capability. It is a design, not a specification: it
marks what the program has decided and what is still an open trade, and it
invents no mechanism.

## Maps are S1-local, and that fixes the primary model

CONOPS section 9.2 places **"selected cached maps"** in **S1, Local Mission
Services**, whose defining property is that they "should remain **locally**
available where practical **even when all external service hosts are absent**."
CONOPS section 9.3 places the **TAK Server** in **S2, Shared Mission Services** --
a service that "may run on a selected MULE" as one *Service Host*, whose state
"shall survive failover before a replacement TAK service may be considered fully
authoritative" (SAD C26-02).

Two consequences follow, and the first is a correction worth stating because the
conflation is easy and consequential:

- **The map service is not the TAK server, and the TAK server serves no tiles.**
  This is not a claim about wiring; the `TBR-TAK-01` work established
  empirically that OpenTAKServer handles no map tiles at all. A node serves maps
  (S1) with **no TAK server present**, and it *must* be able to, because S1 is
  defined to outlive the S2 shared services. "Pull a map from the TAK server"
  mixes two tiers.
- **The primary model is local.** Because S1 must survive the absence of every
  external host, the baseline is that **each capable MULE carries its own tile
  repository and serves its own EUDs from it locally.** That is not a design
  choice this service gets to make; it is what the tier means. The storage that
  makes it possible is `TBR-CARRIER-01` (the M.2-versus-radio slot and the
  `>=256 GB SSD`), and the Program Owner's storage direction -- every node has
  the *option* and the *path* to a large repository -- is exactly what keeps the
  primary model reachable for every node.

## The EUD always addresses its own MULE

`FML-ADR-031` makes EUDs reach services **by name**, through the node's local DNS
and reverse proxy (`services/ingress/`). `FML-ADR-063` gives a deployment one
routable field prefix, so every MULE and EUD in the deployment sits on one
routed field network.

The invariant that falls out: **an EUD's map source names its own MULE's
ingress. It never targets a far node.** Whether a requested tile is served from
the local repository or sourced from a peer over the mesh is a decision the
*MULE* makes, invisible to the EUD. This is also what makes the client's
position-keyed caching manageable -- the source URL the client holds is stable
(its own node), and where the bytes actually come from can change behind it.

## The storage fallback, and what it costs

Some nodes will not carry the repository, or not the specific area an EUD needs.
For those, the node's local map service **sources tiles from a peer that holds
them, over the field network** -- the "map server for the mesh" role. Because map
tiles are **immutable and read-only**, any holder returns identical bytes (the
2026-09-05 bench confirmed a tile fetched across the mesh is byte-identical,
md5, to the holder's stored copy). That has a useful consequence: for maps this
is **holder and coverage discovery, not authority** -- there is no authoritative
copy to elect and no split-brain, which is what makes it simpler than the S2 TAK
failover that `FML-ADR-049` is written for.

What the fallback needs, none of it built, all of it design rather than
specification:

1. **Coverage discovery.** Which reachable peer holds the area and zoom the EUD
   needs. The natural home is the **Service Authority Registry** in the Status
   Aggregator (`FML-ADR-049`), which already collects and distributes peer
   service state over the field network. But that registry is written for S2
   *authority* -- "a process alive but not holding authoritative state is not an
   acceptable backend." Maps need it to advertise **coverage** (which areas and
   zooms a node holds), not authority. Whether coverage rides the existing
   registry or a lighter map-specific advertisement is **open** and belongs to
   `TBR-MAP-01`, and it may warrant its own ADR.
2. **Holder selection and failover.** Pick a reachable holder; if it leaves,
   pick another. Read-only immutable tiles make retry and re-selection safe --
   any holder is as good as any other for the same tile.
3. **An honest availability statement.** In fallback mode, map availability
   **degrades from S1-local to mesh-path availability.** A partition that isolates
   a storage-constrained node from every holder leaves its EUDs with no map --
   which is precisely the failure S1 exists to prevent. So the fallback is a
   **degraded posture, explicitly not equivalent to S1-local**, and the design
   must label it as such wherever it is offered. The `TBR-CARRIER-01` storage
   baseline exists to minimise how often a node is in this posture.

## What the 2026-09-05 bench does and does not show

`test/bench/map-server-mesh.sh` (and the real-iTAK stack built on the live
bench) validated the **transport hop**: a storage-less node fetches a
byte-identical repository tile from a storage node across `batman-adv`, and a
real client renders it. That is the one piece the fallback needs that is real.

It is a **static point-to-point proxy** -- a hardcoded upstream, no coverage
discovery, no holder selection, no failover. It proves the transport the
fallback rides; it is **not** the fallback, and it says nothing about the
any-node-to-any-holder capability. Reading it as "maps fully leverage the mesh"
would be the same overclaim this program guards against.

## Compute

`FML-ADR-021` gives the node one compute element, shared with the routing
daemon. A node that serves tiles to peers over the mesh carries that load **on
top of** serving its own EUDs, and `TBR-COMP-01` must budget it. A storage
server for the mesh is a heavier node than a leaf that only serves itself.

## Decided, and open

**Decided (cited, not re-litigated here):**

- Tile serving is an **S1 local service**, distinct from the S2 TAK server
  (CONOPS section 9.2, 9.3).
- EUDs reach it **by name** through local DNS and the reverse proxy
  (`FML-ADR-031`).
- Service discovery and peer health live in the **Status Aggregator's** registry
  (`FML-ADR-049`).
- One routable **per-deployment field prefix** (`FML-ADR-063`).
- **One compute element** bounds it (`FML-ADR-021`, `TBR-COMP-01`).

**Open (this design surfaces, does not decide):**

- The tile store and server (`TBR-MAP-01`) and the storage carrier
  (`TBR-CARRIER-01`).
- **How map holders advertise coverage, and how a storage-constrained node
  discovers, selects and fails over among them.** This is the new question this
  design raises. It sits inside `TBR-MAP-01`'s mechanism scope and touches
  `FML-ADR-049` and the `TBR-NET-04` share pattern; if the Program Owner wants it
  tracked on its own, it should be minted as its own trade rather than assumed
  here.

See `README.md` in this directory for the service outline and the `z/x/y`
interface this builds on.
