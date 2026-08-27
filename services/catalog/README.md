# Service catalog

The set of services approved to run on a MULE node, and what each one is for.

**Empty. No service has been approved, because no service has been selected.**

## Why a catalog exists

A node has a bounded compute and power budget (`TBR-COMP-01`, `TBR-PWR-01`) and
one compute element shared between the network plane and the mission-service
plane (`FML-ADR-021`). Every service competes with routing for resources, and
the failure mode is specific: a service takes memory, the routing daemon is
starved, mesh links flap, and the node appears to have a radio fault when it
has a scheduling fault.

A catalog makes adding a service a decision with a record, rather than a file
appearing in `quadlets/`.

## What a catalog entry records

| Field | Notes |
| --- | --- |
| Name | Stable identifier used by the Quadlet unit and the ingress configuration. |
| Purpose | One line. Why a node runs this. |
| Image | OCI reference **by immutable digest**, never by tag. |
| Upstream | Project, licence, and where its source lives. |
| Rootless | Yes, or rootful with the reason recorded here. `FML-ADR-029`. |
| Resource envelope | Measured memory and CPU under representative load. `TBR-COMP-01`. |
| Exposed to | The mesh, the EUD access point, or the node only. These are different trust levels; see `os/config/nftables.conf.template`. |
| Durable state | What it stores, and whether that state must survive node loss. `TBR-TAK-01`. |
| Recovery | What a restart costs. `TBR-HA-01`. |
| Region dependency | Whether anything about it is region-specific. |
| ADR | The decision that approved it. |

The **resource envelope** field is deliberately "measured", not "estimated". An
entry with an estimated envelope has not been evaluated.

## Rules

- **Digest, never tag.** Anywhere in this repository. See `services/README.md`.
- **No service is added without a catalog entry.** A Quadlet unit with no entry
  is a defect.
- **No service is added without a resource measurement**, once `TBR-COMP-01`
  has established how the budget is measured.
- **Durable state is declared**, not discovered. `TBR-TAK-01` classifies
  mission state as transient or durable, and a service whose durable state was
  never declared will lose it during a rollback.

## Expected entries

Named so a reader knows what the plane is intended to hold, not as a
commitment:

- A TAK-compatible situational-awareness service. See `services/tak/`.
- Browser-based field services.
- An identity and mission trust layer. See `services/identity/`.
- An operator status surface, fed by the status aggregator, which is a
  placeholder and must not be implemented yet.

None of these has been selected, sized, or approved.
